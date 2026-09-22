#!/usr/bin/env python3
"""Watch 00-Inbox/ and auto-ingest new Markdown notes into the index.

Run in the background:
    python3 scripts/watch.py &
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

VAULT = Path(os.environ.get("SB_VAULT_PATH", Path.home() / "SecondBrain"))
INBOX = VAULT / "00-Inbox"
BRAIN = VAULT / "scripts" / "brain.py"


class IngestHandler(FileSystemEventHandler):
    def on_created(self, event) -> None:
        if event.is_directory or not event.src_path.endswith(".md"):
            return
        print(f"[watch] new note: {event.src_path}")
        subprocess.run(
            [sys.executable, str(BRAIN), "ingest", "--path", event.src_path],
            check=False,
        )


def main() -> None:
    if not INBOX.is_dir():
        raise SystemExit(f"[FAIL] Inbox not found: {INBOX}")
    print(f"[watch] watching {INBOX}")
    observer = Observer()
    observer.schedule(IngestHandler(), str(INBOX), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
