# SecondBrain Template

A local-first, Markdown-based second brain with a runnable Telegram bot and semantic search.

This template gives you:

- A clean Obsidian-compatible folder layout
- A working **brain** — capture notes, embed them locally, search them by meaning
- A minimal Telegram bot (`/save`, `/ask`) you can run on your own machine
- Privacy defaults — everything runs locally, no cloud APIs required

It does **not** include the media-production pipeline (podcast, reel, video). That's separate.

## What's in here

```
SecondBrain-Template/
├── 00-Inbox/          Quick captures
├── 10-Projects/       Active work with a clear outcome
├── 20-Areas/          Ongoing responsibilities
├── 30-Resources/      Reference material
├── 40-Archive/        Completed / inactive
├── 50-Doctrines/      Rules, principles, SOPs
├── 60-References/     Source notes
├── 70-Glossary/       Terms and definitions
├── 80-People/         Optional relationship notes
├── 90-Library/        Long-form material
├── scripts/
│   ├── brain.py       The brain (embed, index, retrieve)
│   ├── telebot.py     Telegram bot (/save, /ask)
│   └── watch.py       Auto-ingest on new notes
├── templates/         Note starters
├── .env.example       Environment template
├── requirements.txt   Python dependencies
└── START-HERE.md      Walkthrough
```

## What you need

1. **Python 3.11+**
2. **Ollama** — https://ollama.com (local model runner)
3. **Two Ollama models:**
   ```bash
   ollama pull nomic-embed-text   # embeddings
   ollama pull llama3.1           # /ask chat model
   ```
4. **A Telegram bot** — talk to @BotFather, get a token
5. **Your numeric Telegram user ID** — talk to @userinfobot

## Quick start

### 1. Clone and set up

```bash
git clone https://github.com/Hinvesting/SecondBrain-Template.git
cd SecondBrain-Template
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Edit `.env`

Fill in:

```
SB_TELEGRAM_BOT_TOKEN=<your token>
SB_TELEGRAM_ALLOWED_USER_ID=<your numeric id>
```

Everything else has a sensible default.

### 3. First reindex

The brain needs an initial pass over your notes (there's one starter note):

```bash
python3 scripts/brain.py reindex
python3 scripts/brain.py status
```

You should see `[PASS] knowledge alignment`.

### 4. Start the bot

```bash
python3 scripts/telebot.py
```

Message your bot:
- `/save This is my first note`
- `/ask what did I save`

### 5. Optional: auto-ingest watcher

In a second terminal:

```bash
python3 scripts/watch.py
```

Anything dropped into `00-Inbox/` gets ingested automatically.

## Using it with Obsidian

Open the folder as a vault: **Obsidian → Open folder as vault → SecondBrain-Template**.

Notes are plain Markdown with YAML frontmatter. Backlinks, graph view, and search all work.

## How the brain works

1. **Capture** — `/save` writes a Markdown file to `00-Inbox/`.
2. **Embed** — `brain.py` sends the text to Ollama's `nomic-embed-text` and gets a 768-dim vector.
3. **Store** — vectors go into `99-System/embeddings.npy`; paths go into `99-System/index.json`.
4. **Retrieve** — `/ask` embeds your question, computes cosine similarity against the matrix, and returns the top matches.
5. **Answer** — the top notes are fed to a local chat model, which answers with citations.

No cloud, no API keys, no telemetry.

## CLI reference

```bash
python3 scripts/brain.py status                     # health check
python3 scripts/brain.py ingest --path <file>       # ingest one note
python3 scripts/brain.py reindex                    # re-embed everything
```

## Privacy notes

- All embeddings and chat run on your machine via Ollama.
- Telegram sees your message text (encrypted in transit, but Telegram's servers see it).
- `.env` is gitignored; `99-System/` (databases, indexes, logs) is gitignored.

## What's not included

This is the "brain" half. The **media-production** half — turning an approved brief into a podcast or a short-form video — is not part of this template. If you want that, [contact the author](https://github.com/Hinvesting).

## License

MIT. See `LICENSE`.
