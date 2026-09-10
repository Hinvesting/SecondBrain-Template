# SecondBrain Template

A privacy-first, local Markdown knowledge vault that works with Obsidian.

This repository is intentionally small and beginner-friendly. It gives you a clean folder structure, starter notes, templates, and privacy guardrails without publishing anyone's private production vault, API keys, passwords, personal logs, databases, embeddings, or proprietary automation code.

## What this is

SecondBrain Template is a starting point for organizing notes, projects, reference material, long-term responsibilities, and reusable knowledge in plain Markdown files.

You can use it with Obsidian for writing, backlinks, local graph view, and full graph view. You can also use the files with any Markdown editor.

## What this is not

This public repository does **not** include a private production SecondBrain engine, private automation workflows, personal notes, private databases, embeddings, provider credentials, or API secrets.

You do not need Python, an API key, GitHub CLI, or a paid AI service to use this template as a knowledge vault.

## Who this is for

- Beginners who want a simple personal knowledge system.
- Obsidian users who want a ready-made folder layout.
- Technical users who prefer Git and Markdown.
- Non-technical users who prefer downloading a ZIP and opening it in Obsidian.

## Folder layout

```text
SecondBrain-Template/
├── 00-Inbox/        Quick captures and notes to sort later
├── 10-Projects/     Work with a defined outcome or finish line
├── 20-Areas/        Ongoing responsibilities and areas of focus
├── 30-Resources/    Useful reference material
├── 40-Archive/      Inactive or completed material
├── 50-Doctrines/    Rules, principles, SOPs, and decision guides
├── 60-References/   Source notes and external references
├── 70-Glossary/     Terms, definitions, and concepts
├── 80-People/       Optional relationship or contact notes
├── 90-Library/      Books, papers, long-form resources, and collections
├── templates/       Reusable note templates
├── START-HERE.md    Your first walkthrough
├── SECURITY.md      Privacy and secret-handling guidance
├── .gitignore       Blocks common secrets and generated/private runtime files
└── LICENSE          MIT license
```

## Quick start for non-technical users

### 1. Download the template

On GitHub, select **Code → Download ZIP**.

Extract the ZIP somewhere you can find easily. Rename the extracted folder if you want, for example:

```text
My-SecondBrain
```

### 2. Install Obsidian

Install Obsidian from the official Obsidian website for your operating system.

### 3. Open the folder as an Obsidian vault

Open Obsidian and choose:

**Open folder as vault**

Select the extracted `SecondBrain-Template` folder, or the new name you gave it.

### 4. Start with the walkthrough

Open:

```text
START-HERE.md
```

Then create your first note in `00-Inbox`.

You are ready to use the vault. No terminal is required.

## Quick start for technical users

Clone the repository:

```bash
git clone https://github.com/Hinvesting/SecondBrain-Template.git my-second-brain
cd my-second-brain
```

Then open `my-second-brain` as an Obsidian vault or edit the Markdown files with your preferred editor.

If you plan to push your personal vault to your own Git repository, create a new private repository instead of pushing personal notes back to this template repository.

## How to use the folders

A simple workflow is:

1. Capture a new thought in `00-Inbox`.
2. Move active outcome-driven work into `10-Projects`.
3. Keep ongoing responsibilities in `20-Areas`.
4. Store reusable information in `30-Resources` or `60-References`.
5. Put durable rules and SOPs in `50-Doctrines`.
6. Move completed or inactive material to `40-Archive`.

Do not worry about perfect organization on day one. Capture first, organize later.

## Linking notes and using the graph

In Obsidian, link one note to another using wiki links:

```markdown
[[Another Note]]
```

To view relationships across the vault:

- Open the Command Palette with `Ctrl+P` or `Cmd+P`.
- Search for **Graph view: Open graph view**.
- For a single note, search for **Local graph: Open local graph**.

The graph shows explicit Markdown links and backlinks. It does not automatically mean two notes are semantically similar.

## Templates

The `templates` folder includes starter formats for common note types. Copy a template, rename the copy, and replace the example fields with your own information.

You may also configure Obsidian's Templates core plugin to use this folder.

## Privacy and security

This repository contains no required credentials.

If you later add scripts, integrations, or AI services:

- Never paste API keys, passwords, access tokens, private keys, or bot tokens into committed Markdown or source files.
- Store secrets outside the vault when possible, or in a local `.env` file that remains ignored by Git.
- Do not commit SQLite databases, embeddings, logs, backups, repair snapshots, or runtime state unless you deliberately understand the privacy consequences.
- Review `SECURITY.md` before publishing a customized vault.
- Before making your own repository public, inspect both the current files **and Git history** for secrets and private information.

The included `.gitignore` provides useful guardrails, but it cannot protect a secret that was committed before the ignore rule existed.

## Troubleshooting

### Obsidian opens but I do not see the vault

Choose **Open another vault → Open folder as vault** and select the folder that contains this `README.md` and `START-HERE.md`.

### My graph is mostly empty

That is normal for a new vault. Graph connections appear after you add links such as `[[Project Example]]` between notes.

### A link appears unresolved

The linked note may not exist yet or its filename may differ from the wiki link. Create the note or correct the link.

### I downloaded a ZIP and cannot find the hidden `.gitignore` file

Files beginning with a dot may be hidden by your file manager. The template still works normally.

### Do I need Python?

No. The public template is a Markdown/Obsidian starter vault. Python is not required.

### Do I need an AI API key?

No. No API key is required to use this template.

## Removing the template

Your notes are ordinary files. To stop using this template:

1. Export or copy any notes you want to keep.
2. Close the vault in Obsidian.
3. Delete the vault folder from your computer if you no longer need it.

Deleting this vault does not uninstall Obsidian. Uninstall Obsidian separately through your operating system if desired.

## Safe customization

Make the structure your own. Rename folders, remove folders you do not need, add tags, and create new templates.

If you add automation later, keep generated state and credentials separate from your human-authored knowledge whenever practical.

## License

This public template is released under the MIT License. See `LICENSE`.

## Maintainer

Maintained by the GitHub account `Hinvesting`.
