# CLAUDE.md

## Project Overview

md-extract is a Markdown file parser and structured extraction tool with CLI and Python API.

## Architecture

- `src/md_extract/extract.py` — Core extraction logic
- `src/md_extract/cli.py` — CLI entry point (argparse, 3 subcommands: extract/toc/meta)
- `options.json` — Single Source of Truth for all CLI options (12 options)
- `scripts/generate-options.mjs` — Code generation from options.json

## Key Design Decisions

- **options.json is SsoT**: All CLI options are defined here, not in code
- **SYNCED markers**: Used in langchain-md-extract for auto-sync
- **Version 0.0.0**: Version is injected at build time via sed in release.yml

## Commands

```bash
make test     # Run tests (pytest + pytest-socket)
make lint     # Run ruff + mypy
make format   # Auto-format with ruff
```

## Conventions

- Commits: conventional commit format (English)
- PRs: single purpose, <10 files, <500 lines
- Python: ruff lint + ruff format + mypy strict
