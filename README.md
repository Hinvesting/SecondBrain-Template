# SecondBrain AI Agent & Content Template

A modular, local-first operating system and multi-agent content pipeline designed for software engineers, technical founders, and builders. 

This repository is the public template derivative of a production SecondBrain vault, stripped of private logs and credentials, giving you a ready-to-deploy foundation for knowledge management and automated media production.

## What It Is
SecondBrain is a local Markdown-first knowledge vault (fully compatible with Obsidian) paired with a Python-powered automation toolkit. It bridges the gap between raw engineering notes, automated audio generation, and short-form video prompt engineering.

## What It Does
* **Dual-Agent Content Pipeline:** 
  * **Agent 1 (The Showrunner):** Ingests raw Markdown operational logs and translates them into engaging, frontline 6-scene narrative scripts.
  * **Agent 2 (The Cinematographer):** Dynamically applies an advanced cinematic dictionary (ECU, CU, MS, CS, OTS, camera movements, lighting) and brand specs to generate precision prompts for multimodal AI video generators (like Gemini Omni).
* **Automated Audio Overviews:** Includes a robust CLI engine wrapping third-party tools (`notebooklm-py`) to automatically ingest Markdown notes, handle session auth, track context IDs, and compile professional podcast episodes.
* **Knowledge Organization:** Features a clean, structured directory layout optimized for rapid capture, long-term maintenance, and graph-view visualization.

## Why It's Useful
If you build in public, manage complex technical projects, or want to automate your content creation workflows without sacrificing architectural integrity, this template provides:
1. **Zero-Bloat Knowledge Management:** Keep your notes local, secure, and searchable.
2. **Instant Content Repurposing:** Turn system logs and bug fixes into production-ready video scripts and podcasts with a single terminal command.
3. **Robust CLI Automation:** Handle brittle third-party API rebrands and session management with built-in Playwright resiliency and regex parsing.

## Quick Start Guide

### 1. Prerequisites
* Python 3.10+
* Git & GitHub CLI (`gh`)

### 2. Clone and Setup
```bash
git clone [https://github.com/Hinvesting/SecondBrain-Template.git](https://github.com/Hinvesting/SecondBrain-Template.git)
cd SecondBrain-Template

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install "notebooklm-py[browser]" playwright
playwright install


3. Usage Example
Run the dual-agent content pipeline on any operational markdown log:
Bash
python scripts/content_agent.py 00-Inbox/your_log_file.md


Repository Structure
Plaintext
├── 00-Inbox/        # Raw operational logs, scratchpads, and quick captures
├── 99-System/       # System scripts, media outputs, and configuration assets
├── scripts/         # Automation engines (podcast compiler, dual-agent pipeline)
├── LICENSE          # MIT License
└── README.md        # Documentation


Contributing
Built and maintained by Aaron Sweeney. Feel free to fork, customize, and adapt for your own engineering workflows.
