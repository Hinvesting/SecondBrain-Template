#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np


VAULT = Path.home() / "SecondBrain"
SYSTEM = VAULT / "99-System"

INDEX_PATH = SYSTEM / "index.json"
EMBEDDINGS_PATH = SYSTEM / "embeddings.npy"

OLLAMA_HOST = os.environ.get(
    "OLLAMA_HOST",
    "http://127.0.0.1:11434",
).rstrip("/")

MODEL = os.environ.get(
    "SB_EMBEDDING_MODEL",
    "nomic-embed-text",
)

WIDTH = 768

#
# These are the human-knowledge zones of the vault.
#
KNOWLEDGE_ROOTS = (
    "00-Inbox",
    "10-Projects",
    "20-Areas",
    "30-Resources",
    "40-Archive",
    "50-Doctrines",
    "templates",
)

#
# These are never semantic-knowledge sources.
#
EXCLUDED_NAMES = {
    ".venv",
    "venv",
    ".git",
    ".obsidian",
    "98-Automations",
    "99-System",
    "moneyprinter",
    "node_modules",
    "site-packages",
    "__pycache__",
}

LOCK = SYSTEM / ".knowledge-reindex.lock"


class KnowledgeFailure(RuntimeError):
    pass


def say(message: str) -> None:
    print(message, flush=True)


def inside_vault(path: Path) -> bool:
    try:
        path.resolve().relative_to(VAULT.resolve())
        return True
    except ValueError:
        return False


#
# Root-level repo documentation — structural, not semantic knowledge.
# These live at the vault root and would otherwise be pulled in by
# the `VAULT.glob("*.md")` scan in discover().
#
EXCLUDED_TOP_LEVEL = {
    "ENGINEERING.md",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "LICENSE",
    "LICENSE.md",
}


def prohibited(rel: Path) -> bool:
    for part in rel.parts:
        if part in EXCLUDED_NAMES:
            return True

        if part.startswith("."):
            return True

    return False


def discover() -> list[str]:
    found: set[str] = set()

    #
    # Root-level Markdown notes.
    #
    for path in VAULT.glob("*.md"):
        if not path.is_file():
            continue

        if path.name in EXCLUDED_TOP_LEVEL:
            continue

        try:
            content = path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            continue

        if not content.strip():
            continue

        found.add(
            path.relative_to(VAULT).as_posix()
        )

    #
    # Explicit human-knowledge roots only.
    #
    for root_name in KNOWLEDGE_ROOTS:
        root = VAULT / root_name

        if not root.is_dir():
            continue

        for path in root.rglob("*.md"):
            if not path.is_file():
                continue

            if not inside_vault(path):
                continue

            rel = path.relative_to(VAULT)

            if prohibited(rel):
                continue

            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            except OSError:
                continue

            if not content.strip():
                continue

            found.add(rel.as_posix())

    return sorted(found)


def embed(text: str, rel: str) -> np.ndarray:
    encoded = json.dumps(
        {
            "model": MODEL,
            "input": text,
            "options": {
                "num_ctx": int(
                    os.environ.get("SB_EMBED_NUM_CTX", "8192")
                ),
            },
        }
    ).encode("utf-8")

    last_error = None

    for attempt in range(1, 4):
        request = urllib.request.Request(
            f"{OLLAMA_HOST}/api/embed",
            data=encoded,
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=300,
            ) as response:
                payload = json.loads(
                    response.read().decode("utf-8")
                )

            returned = payload.get(
                "embeddings"
            ) or []

            if not returned:
                raise KnowledgeFailure(
                    "Ollama returned no embedding"
                )

            vector = np.asarray(
                returned[0],
                dtype=np.float32,
            ).reshape(-1)

            if vector.shape != (WIDTH,):
                raise KnowledgeFailure(
                    f"vector shape={vector.shape}, "
                    f"expected ({WIDTH},)"
                )

            return vector

        except (
            TimeoutError,
            socket.timeout,
            urllib.error.URLError,
            KnowledgeFailure,
        ) as exc:
            last_error = exc

            say(
                f"[WARN] attempt {attempt}/3 "
                f"for {rel}: {exc}"
            )

            if attempt < 3:
                delay = 5 * attempt

                say(
                    f"[INFO] retrying in {delay}s"
                )

                time.sleep(delay)

    raise KnowledgeFailure(
        f"embedding failed after 3 attempts "
        f"for {rel}: {last_error}"
    )


def acquire_lock() -> None:
    if LOCK.exists():
        _clear_lock_if_stale()
        if LOCK.exists():
            raise KnowledgeFailure(
                f"another reindex is active: {LOCK}"
            )
    try:
        LOCK.mkdir()
        (LOCK / "pid").write_text(str(os.getpid()))
    except FileExistsError:
        raise KnowledgeFailure(
            f"another reindex is active: {LOCK}"
        )


def release_lock() -> None:
    shutil.rmtree(LOCK, ignore_errors=True)


def _clear_lock_if_stale() -> None:
    """Remove LOCK if its owning PID is dead or the lock is old."""
    pidfile = LOCK / "pid"
    if pidfile.is_file():
        try:
            pid = int(pidfile.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            pid = None
        if pid is not None:
            try:
                os.kill(pid, 0)
                return  # owner alive — keep the lock
            except ProcessLookupError:
                say(f"[INFO] clearing stale reindex lock (dead pid={pid})")
                shutil.rmtree(LOCK, ignore_errors=True)
                return
            except PermissionError:
                return  # can't signal, assume alive
        # malformed pid file — fall through to age check
    try:
        age = time.time() - LOCK.stat().st_mtime
    except OSError:
        return
    if age > 900:
        say(f"[INFO] clearing stale reindex lock (age={int(age)}s)")
        shutil.rmtree(LOCK, ignore_errors=True)


def fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)

    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def read_existing_metadata() -> dict:
    if not INDEX_PATH.exists():
        return {}

    try:
        value = json.loads(
            INDEX_PATH.read_text(
                encoding="utf-8"
            )
        )

        return value if isinstance(
            value,
            dict,
        ) else {}

    except Exception:
        return {}


def rebuild() -> None:
    SYSTEM.mkdir(
        parents=True,
        exist_ok=True,
    )

    acquire_lock()

    try:
        paths = discover()

        if not paths:
            raise KnowledgeFailure(
                "no knowledge notes discovered"
            )

        say("")
        say("=== CURATED KNOWLEDGE CORPUS ===")

        for rel in paths:
            say(f"[NOTE] {rel}")

        say("")
        say(
            f"[INFO] Eligible knowledge notes: "
            f"{len(paths)}"
        )

        vectors: list[np.ndarray] = []

        say("")
        say("=== EMBEDDING ===")

        for number, rel in enumerate(
            paths,
            start=1,
        ):
            full = VAULT / rel

            text = full.read_text(
                encoding="utf-8",
                errors="replace",
            )

            vector = embed(
                text,
                rel,
            )

            vectors.append(vector)

            say(
                f"[PASS] "
                f"{number:02d}/{len(paths):02d} "
                f"{rel} -> {vector.shape}"
            )

        matrix = np.vstack(
            vectors
        ).astype(
            np.float32,
            copy=False,
        )

        expected = (
            len(paths),
            WIDTH,
        )

        if matrix.shape != expected:
            raise KnowledgeFailure(
                f"matrix shape={matrix.shape}, "
                f"expected={expected}"
            )

        metadata = read_existing_metadata()
        metadata["id_to_path"] = paths

        #
        # Build and validate both replacements
        # before modifying either canonical file.
        #
        with tempfile.TemporaryDirectory(
            prefix=".knowledge-build-",
            dir=SYSTEM,
        ) as temp_name:
            temp = Path(temp_name)

            candidate_index = (
                temp / "index.json"
            )

            candidate_vectors = (
                temp / "embeddings.npy"
            )

            candidate_index.write_text(
                json.dumps(
                    metadata,
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            with candidate_vectors.open(
                "wb"
            ) as handle:
                np.save(
                    handle,
                    matrix,
                )

                handle.flush()
                os.fsync(
                    handle.fileno()
                )

            candidate_paths = json.loads(
                candidate_index.read_text(
                    encoding="utf-8"
                )
            )["id_to_path"]

            candidate_matrix = np.load(
                candidate_vectors,
                mmap_mode="r",
            )

            if candidate_matrix.shape != (
                len(candidate_paths),
                WIDTH,
            ):
                raise KnowledgeFailure(
                    "candidate pair alignment FAIL"
                )

            #
            # Temporary rollback copies for
            # pair-commit protection.
            #
            old_index = temp / "old-index.json"
            old_vectors = temp / "old-embeddings.npy"

            if INDEX_PATH.exists():
                shutil.copy2(
                    INDEX_PATH,
                    old_index,
                )

            if EMBEDDINGS_PATH.exists():
                shutil.copy2(
                    EMBEDDINGS_PATH,
                    old_vectors,
                )

            try:
                os.replace(
                    candidate_vectors,
                    EMBEDDINGS_PATH,
                )

                os.replace(
                    candidate_index,
                    INDEX_PATH,
                )

                fsync_dir(SYSTEM)

                final_paths = json.loads(
                    INDEX_PATH.read_text(
                        encoding="utf-8"
                    )
                )["id_to_path"]

                final_matrix = np.load(
                    EMBEDDINGS_PATH,
                    mmap_mode="r",
                )

                if final_matrix.shape != (
                    len(final_paths),
                    WIDTH,
                ):
                    raise KnowledgeFailure(
                        "post-commit alignment FAIL"
                    )

            except Exception:
                if old_vectors.exists():
                    shutil.copy2(
                        old_vectors,
                        EMBEDDINGS_PATH,
                    )

                if old_index.exists():
                    shutil.copy2(
                        old_index,
                        INDEX_PATH,
                    )

                fsync_dir(SYSTEM)

                raise

        say("")
        say(
            f"[PASS] Atomic knowledge commit: "
            f"{len(paths)} x {WIDTH}"
        )

    finally:
        release_lock()


def status() -> None:
    if not INDEX_PATH.is_file():
        raise KnowledgeFailure(
            "index.json missing"
        )

    if not EMBEDDINGS_PATH.is_file():
        raise KnowledgeFailure(
            "embeddings.npy missing"
        )

    paths = json.loads(
        INDEX_PATH.read_text(
            encoding="utf-8"
        )
    ).get("id_to_path")

    if not isinstance(paths, list):
        raise KnowledgeFailure(
            "id_to_path is invalid"
        )

    matrix = np.load(
        EMBEDDINGS_PATH,
        mmap_mode="r",
    )

    print(
        "index rows      =",
        len(paths),
    )

    print(
        "embedding shape =",
        matrix.shape,
    )

    if matrix.shape != (
        len(paths),
        WIDTH,
    ):
        raise KnowledgeFailure(
            "index/vector alignment FAIL"
        )

    polluted = []

    for rel_string in paths:
        rel = Path(rel_string)

        if prohibited(rel):
            polluted.append(rel_string)

        if rel.parts and (
            rel.parts[0] not in
            KNOWLEDGE_ROOTS
        ) and len(rel.parts) > 1:
            polluted.append(rel_string)

    if polluted:
        raise KnowledgeFailure(
            "polluted index entries: "
            + repr(sorted(set(polluted)))
        )

    print(
        "[PASS] knowledge alignment"
    )

    print(
        "[PASS] curated corpus boundary"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="brain.py",
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser("reindex")
    sub.add_parser("status")

    ingest = sub.add_parser("ingest")

    ingest.add_argument(
        "--path",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    try:
        if args.command == "status":
            status()
            return 0

        if args.command == "reindex":
            rebuild()
            return 0

        if args.command == "ingest":
            target = args.path.expanduser().resolve()

            if not inside_vault(target):
                raise KnowledgeFailure(
                    "ingest path must be inside vault"
                )

            if not target.exists():
                raise KnowledgeFailure(
                    f"ingest target missing: {target}"
                )

            #
            # The corpus is intentionally small.
            # A complete atomic rebuild is safer
            # than incremental index/vector mutation.
            #
            rebuild()
            return 0

        raise KnowledgeFailure(
            "unsupported command"
        )

    except Exception as exc:
        print(
            f"[FAIL] {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
