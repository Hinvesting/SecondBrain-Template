# Start Here

Welcome to your SecondBrain. Two things live in this folder:

1. A **vault** — plain Markdown notes, openable in Obsidian.
2. A **brain** — Python scripts that index and search those notes locally.

You can use the vault alone if you want. The brain makes it searchable by meaning and reachable from Telegram.

## Minute one: open the vault

If you have Obsidian:
- **Open folder as vault** → pick this folder.

Browse the numbered folders. Each has a `README.md` explaining what goes there.

## Minute five: set up the brain (optional)

You need Python 3.11+ and Ollama.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install Ollama from https://ollama.com, then:

```bash
ollama pull nomic-embed-text
ollama pull llama3.1
```

## Minute ten: connect Telegram

1. Message @BotFather on Telegram, create a bot, copy the token.
2. Message @userinfobot, copy your numeric user ID.
3. `cp .env.example .env` and fill in both values.

## Minute fifteen: run it

```bash
python3 scripts/brain.py reindex
python3 scripts/telebot.py
```

Open Telegram, find your bot, and:

```
/save Testing my new second brain
```

Then:

```
/ask what did I just save
```

## The daily loop

- Capture on Telegram with `/save`, or drop a `.md` file into `00-Inbox/`.
- Ask questions with `/ask`.
- Open Obsidian to browse and link notes.

That's it. The brain handles the rest.

## Folder meanings

- `00-Inbox` — landing zone for new captures
- `10-Projects` — has a defined end
- `20-Areas` — ongoing responsibilities
- `30-Resources` — reference material
- `40-Archive` — done or inactive
- `50-Doctrines` — rules and SOPs
- `60-References` — sources
- `70-Glossary` — terms
- `80-People` — optional contacts
- `90-Library` — books, papers, collections
- `templates` — reusable note starters

## When something breaks

- `brain.py status` tells you if the index is healthy.
- If `reindex` fails on a large file, you can exclude it — see `README.md`.
- Ollama must be running (`ollama serve` or the desktop app).

## Where to go next

- Read `SECURITY.md` for the privacy model.
- Read `README.md` for the CLI reference.
- Organize over time. The structure is a suggestion, not a rule.
