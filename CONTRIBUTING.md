# Contributing

Thank you for your interest in contributing to jostack-mdparse!

## Development Setup

```bash
git clone https://github.com/hyunhee-jo/jostack-mdparse.git
cd jostack-mdparse
pip install -e .
pip install pytest pytest-socket ruff mypy
```

## Running Tests

```bash
make test
```

## Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting, and [mypy](https://mypy-lang.org/) for type checking.

```bash
make lint    # Check
make format  # Auto-fix
```

## Pull Requests

- One PR per feature/fix (keep PRs small: <10 files, <500 lines)
- All tests must pass
- Follow conventional commit messages
