# SecondBrain AI Agent & Content Template

A modular, local-first operating system and multi-agent content pipeline designed for software engineers, technical founders, and builders. 

This repository is the public template derivative of a production SecondBrain vault. You can clone this repository to establish your own local knowledge vault and utilize the included `requirements.txt` to install the exact Python dependencies needed for your automation engines.

## What It Is
SecondBrain is a local Markdown-first knowledge vault (fully compatible with Obsidian) paired with a Python-powered automation toolkit. It bridges the gap between raw engineering notes, automated audio generation, and short-form video prompt engineering.

## What It Does
* **Dual-Agent Content Pipeline:** 
  * **Agent 1 (The Showrunner):** Ingests raw Markdown operational logs and translates them into engaging, frontline 6-scene narrative scripts.
  * **Agent 2 (The Cinematographer):** Dynamically applies an advanced cinematic dictionary (ECU, CU, MS, CS, OTS, camera movements, lighting) and brand specs to generate precision prompts for multimodal AI video generators (like Gemini Omni).
* **Automated Audio Overviews:** Includes a robust CLI engine wrapping third-party tools (`notebooklm-py`) to automatically ingest Markdown notes, handle session auth, track context IDs, and compile professional podcast episodes.
* **Knowledge Organization:** Features a clean, structured directory layout optimized for rapid capture, long-term maintenance, and graph-view visualization.

---

## Why It's Useful
If you build in public, manage complex technical projects, or want to automate your content creation workflows without sacrificing architectural integrity, this template provides:
1. **Zero-Bloat Knowledge Management:** Keep your notes local, secure, and searchable.
2. **Instant Content Repurposing:** Turn system logs and bug fixes into production-ready video scripts and podcasts with a single terminal command.
3. **Robust CLI Automation:** Handle brittle third-party API rebrands and session management with built-in Playwright resiliency and regex parsing.

---

## Quick Start & Installation Guide

To set this up for your own vault, follow these steps to clone the template and stock your environment with the required dependencies:

### 1. Prerequisites
* Python 3.10+
* Git & GitHub CLI (`gh`)

### 2. Clone the Template for Your Vault
Clone the public template repository into your local machine to initialize your own vault structure:
```bash
git clone [https://github.com/Hinvesting/SecondBrain-Template.git](https://github.com/Hinvesting/SecondBrain-Template.git) my-second-brain
cd my-second-brain


3. Set Up the Virtual Environment and Install Requirements
Stock your local environment with the required automation packages defined in requirements.txt:
Bash
# Create and activate your virtual environment (.venv)
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install all required automation dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install browser automation binaries for audio/podcast engines
playwright install


4. Usage Example
Run the dual-agent content pipeline on any operational markdown log in your new vault:
Bash
python scripts/content_agent.py 00-Inbox/your_log_file.md


Repository Structure
Plaintext
├── 00-Inbox/        # Raw operational logs, scratchpads, and quick captures
├── 99-System/       # System scripts, media outputs, and configuration assets
├── scripts/         # Automation engines (podcast compiler, dual-agent pipeline)
├── requirements.txt # Python package dependencies for all automation scripts
├── LICENSE          # MIT License
└── README.md        # Documentation


Contributing
Built and maintained by Aaron Sweeney. Feel free to fork, customize, and adapt for your own engineering workflows.
