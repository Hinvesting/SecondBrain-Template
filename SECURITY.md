# Security and Privacy Guide

This public template is designed to stay free of credentials and private production data.

## Never commit these

- API keys
- passwords
- access or refresh tokens
- bot tokens
- private keys or certificates
- recovery codes
- `.env` files containing real secrets
- local databases
- embedding matrices
- runtime logs
- backups
- repair snapshots
- machine-specific workspace state
- personal notes you do not intend to publish

## Recommended secret storage

If you later add automation, keep secrets outside the vault whenever practical.

For local development, environment variables or a local `.env` file may be appropriate. The included `.gitignore` blocks common `.env` patterns, but you must still verify what Git is tracking.

## Before publishing your own vault

Run these checks from the repository root:

```bash
git status --short
git ls-files
```

Review every tracked file.

Search the current tracked files for common secret labels:

```bash
git grep -nEi 'api[_-]?key|password|passwd|secret|token|private[_-]?key' || true
```

This is only a basic check. A real secret can exist without an obvious label.

## Git history matters

Adding a file to `.gitignore` does not remove it from earlier commits.

If a real credential was ever committed to a repository that other people could access:

1. Revoke or rotate the credential first.
2. Remove the secret from the current repository.
3. Rewrite Git history if appropriate.
4. Re-check all branches and tags.
5. Inform affected users if exposure created material risk.

Treat an exposed credential as compromised even if the repository was public only briefly.

## Public-template boundary

This template should contain only generic starter material. Private production notes, automation internals, proprietary prompts, customer information, databases, logs, embeddings, backups, and provider credentials belong outside this public repository unless deliberately released.

## Reporting a problem

If you discover sensitive information in this public template, do not repost the value in an issue. Contact the repository maintainer privately through an appropriate GitHub contact method and identify the affected file or commit without reproducing the secret.
