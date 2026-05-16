# Security Policy

## Supported Versions

The active development branch is `main`.

## Sensitive Data

Do not commit:

- API keys
- `.env` files
- Private source credentials
- Local SQLite databases
- Generated digests containing private research

Runtime files are ignored by `.gitignore`.

## Reporting Issues

If this is a private repository, open a private issue or contact the repository owner directly.

If this becomes public, use GitHub private vulnerability reporting if enabled.

## Trading Safety

This project does not execute trades. Any downstream trading system should include independent validation, risk controls, logging, and manual review before deployment.
