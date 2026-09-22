#!/usr/bin/env python3
"""SecondBrain Template — Telegram bot (starter edition).

Two commands:
  /save <text>   capture a note into 00-Inbox/
  /ask <query>   answer a question from your indexed notes

Requirements:
  - A local Ollama instance (https://ollama.com)
  - `ollama pull nomic-embed-text`  (embeddings)
  - A chat model, e.g. `ollama pull llama3.1`
  - brain.py has been run at least once so 99-System/index.json exists

Environment (see .env.example):
  SB_TELEGRAM_BOT_TOKEN
  SB_TELEGRAM_ALLOWED_USER_ID
  SB_OLLAMA_HOST           (default: http://127.0.0.1:11434)
  SB_EMBEDDING_MODEL       (default: nomic-embed-text)
  SB_CHAT_MODEL            (default: llama3.1)
  SB_VAULT_PATH            (default: ~/SecondBrain)
  SB_EMBED_NUM_CTX         (default: 8192)
"""
from __future__ import annotations

import asyncio
import datetime as dt
import fcntl
import json
import logging
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Coroutine

import numpy as np
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.error import Conflict, NetworkError, RetryAfter, TimedOut
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- configuration --------------------------------------------------

VAULT = Path(os.environ.get("SB_VAULT_PATH", Path.home() / "SecondBrain"))
SYSTEM = VAULT / "99-System"
INBOX = VAULT / "00-Inbox"
INDEX_PATH = SYSTEM / "index.json"
EMBEDDINGS_PATH = SYSTEM / "embeddings.npy"
BRAIN = VAULT / "scripts" / "brain.py"
LOCK_PATH = Path(tempfile.gettempdir()) / "secondbrain-template-bot.lock"

TelegramCallback = Callable[
    [Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]
]


def _load_env() -> None:
    """Load credentials from every standard location.

    Search order (first-hit-wins per key):
      1. $SB_VAULT_PATH/.env       (or ~/SecondBrain/.env)
      2. ~/.config/secondbrain-engine/engine.env
      3. ./.env in the current directory

    override=False means later files only fill gaps, they never clobber
    earlier values. Shell-exported variables still win over all of them.
    """
    candidates = [
        VAULT / ".env",
        Path.home() / ".config" / "secondbrain-engine" / "engine.env",
        Path.cwd() / ".env",
    ]
    for candidate in candidates:
        if candidate.is_file():
            load_dotenv(candidate, override=False)
_load_env

def cfg(key: str, default: str | None = None) -> str | None:
    v = os.environ.get(key)
    return v if v not in (None, "") else default


def cfg_int(key: str, default: int) -> int:
    try:
        return int(cfg(key, str(default)) or default)
    except ValueError:
        return default


def vault_path() -> Path:
    p = cfg("SB_VAULT_PATH")
    return Path(p).expanduser() if p else VAULT


def ollama_host() -> str:
    return (cfg("SB_OLLAMA_HOST", "http://127.0.0.1:11434") or "").rstrip("/")


def embedding_model() -> str:
    return cfg("SB_EMBEDDING_MODEL", "nomic-embed-text") or "nomic-embed-text"


def chat_model() -> str:
    return cfg("SB_CHAT_MODEL", "llama3.1") or "llama3.1"


# --- logging --------------------------------------------------------

log = logging.getLogger("secondbrain.bot")


_TOKEN_URL_RE = re.compile(r"/bot\d+:[A-Za-z0-9_-]+")


class _RedactToken(logging.Filter):
    """Redact Telegram bot tokens from log records before emission.

    httpx and python-telegram-bot log every request URL at INFO level.
    Those URLs contain the bot token; without this filter, running the bot
    leaks the credential to stdout, journald, and any log file it's piped to.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _TOKEN_URL_RE.sub("/bot<REDACTED>", record.msg)

        args = record.args
        if args:
            if isinstance(args, dict):
                record.args = {
                    k: _TOKEN_URL_RE.sub("/bot<REDACTED>", v)
                    if isinstance(v, str)
                    else v
                    for k, v in args.items()
                }
            elif isinstance(args, tuple):
                record.args = tuple(
                    _TOKEN_URL_RE.sub("/bot<REDACTED>", a)
                    if isinstance(a, str)
                    else a
                    for a in args
                )
        return True


def _configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    handler.addFilter(_RedactToken())

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


# --- auth -----------------------------------------------------------

def _parse_allowed_ids() -> frozenset[int]:
    raw = cfg("SB_TELEGRAM_ALLOWED_USER_ID", "") or ""
    ids: set[int] = set()
    for token in re.split(r"[,\s]+", raw.strip()):
        if not token:
            continue
        try:
            ids.add(int(token))
        except ValueError:
            log.warning("ignoring non-numeric allowed id: %r", token)
    return frozenset(ids)


ALLOWED_IDS: frozenset[int] = _parse_allowed_ids()


def _effective_user_id(update: Update) -> int | None:
    return update.effective_user.id if update.effective_user else None


def _allowed(update: Update) -> bool:
    uid = _effective_user_id(update)
    return uid is not None and uid in ALLOWED_IDS


def guard(fn: TelegramCallback) -> TelegramCallback:
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not _allowed(update):
            if update.effective_chat:
                await update.effective_chat.send_message(
                    "Not authorized."
                )
            return
        await fn(update, ctx)
    wrapper.__name__ = fn.__name__
    return wrapper


# --- single instance ------------------------------------------------

def _acquire_lock() -> None:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(LOCK_PATH), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit(
            "Another SecondBrain bot instance is already running "
            f"(lock: {LOCK_PATH})"
        )
    os.truncate(fd, 0)
    os.write(fd, str(os.getpid()).encode())
    # fd intentionally kept open for process lifetime


# --- note capture ---------------------------------------------------

def _ensure_inside_vault(path: Path) -> Path:
    root = vault_path().resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"Refusing to write outside vault: {path}") from exc
    return resolved


def _slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:max_len].rstrip("-") or "note"


def _frontmatter(title: str) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    safe = title.replace('"', "'")
    return (
        "---\n"
        f'title: "{safe}"\n'
        "aliases: []\n"
        "tags: []\n"
        "status: draft\n"
        "category: inbox\n"
        f"created: {now}\n"
        f"updated: {now}\n"
        "summary:\n"
        "---\n\n"
    )


def _atomic_write(target: Path, content: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, target)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def _save_note(raw_text: str) -> Path:
    text = raw_text.strip()
    if not text:
        raise ValueError("empty note")
    # First line becomes the title
    first_line = text.splitlines()[0]
    title = first_line[:80]
    stem = _slugify(title)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{stamp}-{stem}.md"
    target = _ensure_inside_vault(vault_path() / "00-Inbox" / filename)
    body = _frontmatter(title) + text + "\n"
    _atomic_write(target, body)
    return target


def _run_brain_ingest(note_path: Path) -> tuple[bool, str]:
    if not BRAIN.is_file():
        return False, f"brain.py not found at {BRAIN}"
    try:
        proc = subprocess.run(
            [sys.executable, str(BRAIN), "ingest", "--path", str(note_path)],
            capture_output=True,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        return False, "brain.py ingest timed out"
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "").strip()[:400]
    return True, ""


# --- embeddings / retrieval ----------------------------------------

def _embed_sync(text: str) -> np.ndarray:
    payload = {
        "model": embedding_model(),
        "input": text,
        "options": {"num_ctx": cfg_int("SB_EMBED_NUM_CTX", 8192)},
    }
    r = requests.post(
        f"{ollama_host()}/api/embed", json=payload, timeout=180
    )
    r.raise_for_status()
    data = r.json()
    vectors = data.get("embeddings") or []
    if not vectors:
        raise RuntimeError("Ollama returned no embedding")
    arr = np.asarray(vectors[0], dtype=np.float32).reshape(-1)
    return arr


def _chat_sync(prompt: str) -> str:
    payload = {
        "model": chat_model(),
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    r = requests.post(
        f"{ollama_host()}/api/chat", json=payload, timeout=300
    )
    r.raise_for_status()
    data = r.json()
    return (data.get("message") or {}).get("content", "").strip()


def _load_index() -> tuple[list[str], np.ndarray]:
    if not INDEX_PATH.is_file() or not EMBEDDINGS_PATH.is_file():
        raise FileNotFoundError(
            "Index not found. Run: python3 scripts/brain.py reindex"
        )
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if isinstance(index, dict):
        index = index.get("notes") or index.get("items") or []
    paths = [entry["path"] if isinstance(entry, dict) else entry
             for entry in index]
    matrix = np.load(EMBEDDINGS_PATH)
    if matrix.shape[0] != len(paths):
        raise RuntimeError(
            f"Index/embedding mismatch: {len(paths)} paths, "
            f"matrix shape {matrix.shape}"
        )
    return paths, matrix


def _top_k(query: str, k: int = 5) -> list[tuple[str, float]]:
    paths, matrix = _load_index()
    qv = _embed_sync(query)
    if qv.shape[0] != matrix.shape[1]:
        raise RuntimeError(
            f"Query dim {qv.shape[0]} != matrix dim {matrix.shape[1]}"
        )
    qn = float(np.linalg.norm(qv))
    if qn <= 1e-12:
        raise RuntimeError("zero-magnitude query embedding")
    row_norms = np.linalg.norm(matrix, axis=1)
    scores = (matrix @ qv) / (row_norms * qn)
    order = np.argsort(-scores)[:k]
    return [(paths[int(i)], float(scores[int(i)])) for i in order]


# --- command handlers ----------------------------------------------

START_TEXT = (
    "SecondBrain bot ready.\n\n"
    "/save <text>  — capture a note\n"
    "/ask <query>  — ask your notes\n"
)


@guard
async def start_cmd(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        await update.effective_chat.send_message(START_TEXT)


@guard
async def save_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(ctx.args).strip()
    if not text:
        if update.effective_chat:
            await update.effective_chat.send_message("Usage: /save <text>")
        return
    await _do_save(update, text)


@guard
async def save_text_handler(
    update: Update, _ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    msg = update.effective_message
    if msg is None or not msg.text:
        return
    await _do_save(update, msg.text)


async def _do_save(update: Update, text: str) -> None:
    chat = update.effective_chat
    if chat is None:
        return
    try:
        note = await asyncio.to_thread(_save_note, text)
    except Exception as exc:
        await chat.send_message(f"Save failed: {exc}")
        return

    await chat.send_message(f"Saved: {note.name}")

    ok, err = await asyncio.to_thread(_run_brain_ingest, note)
    if ok:
        await chat.send_message("Indexed.")
    else:
        await chat.send_message(
            f"Saved, but ingestion was not confirmed.\n{err}"
        )


@guard
async def ask_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(ctx.args).strip()
    chat = update.effective_chat
    if chat is None:
        return
    if not query:
        await chat.send_message("Usage: /ask <question>")
        return

    await chat.send_action(ChatAction.TYPING)

    try:
        hits = await asyncio.to_thread(_top_k, query, 5)
    except Exception as exc:
        await chat.send_message(f"Search failed: {exc}")
        return

    if not hits:
        await chat.send_message("No indexed notes matched.")
        return

    vroot = vault_path()
    context_blocks: list[str] = []
    for path_str, _score in hits:
        note_path = vroot / path_str
        try:
            body = note_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if body.startswith("---"):
            parts = body.split("---", 2)
            if len(parts) == 3:
                body = parts[2].lstrip()
        context_blocks.append(f"# {path_str}\n{body[:2000]}")

    context = "\n\n".join(context_blocks)
    prompt = (
        "You are answering a question using a private note archive.\n"
        "Rules:\n"
        "1. Answer only from the context below.\n"
        "2. Cite the note path in [brackets] after each claim.\n"
        "3. Be concise.\n"
        "4. If the context does not answer, say exactly: "
        "'No indexed notes answer that question.'\n\n"
        f"Question: {query}\n\n"
        f"Context:\n{context}\n\n"
        "Answer:"
    )

    try:
        answer = await asyncio.to_thread(_chat_sync, prompt)
    except Exception as exc:
        await chat.send_message(f"Answer failed: {exc}")
        return

    await chat.send_message(answer or "No answer produced.")


async def error_handler(
    _update: object, ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    log.error("bot error: %s", ctx.error, exc_info=ctx.error)


# --- startup / shutdown --------------------------------------------

async def post_init(app: Application) -> None:
    me = await app.bot.get_me()
    log.info("bot authenticated id=%s username=@%s", me.id, me.username)


async def post_shutdown(_app: Application) -> None:
    log.info("bot shutting down")


def build_application() -> Application:
    token = cfg("SB_TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("SB_TELEGRAM_BOT_TOKEN is not set")
    if not ALLOWED_IDS:
        raise SystemExit(
            "SB_TELEGRAM_ALLOWED_USER_ID is not set — refusing to start"
        )
    app = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", start_cmd))
    app.add_handler(CommandHandler("save", save_cmd))
    app.add_handler(CommandHandler("ask", ask_cmd))
    # Bare text = save
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, save_text_handler)
    )
    app.add_error_handler(error_handler)
    return app


def main() -> int:
    _configure_logging()
    _acquire_lock()
    log.info("starting bot, vault=%s", vault_path())
    app = build_application()
    app.run_polling(drop_pending_updates=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
