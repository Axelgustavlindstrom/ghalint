# ghalint

Lint GitHub Actions workflow files for common issues, best practices, and correctness.

## About

`ghalint` analyzes `.github/workflows/*.yml` and `*.yaml` files and reports
problems that can cause CI failures, security risks, or just noisy logs.

It focuses on actionable checks:

- Workflow naming and metadata
- Job-level run ordering
- Action/step shell quoting
- Cache key usage
- Secrets masking
- Failure behavior on composite actions

Output is colorized by default and supports `--json` for tooling.

## Features

- Scans one workflow file or an entire `.github/workflows/` directory
- JSON and plain text reporting via `rich`
- Fast, zero-config defaults with optional strictness knobs
- Minimal dependencies: only `pyyaml`, `rich`, `requests`

## Installation

```bash
python -m pip install ghalint
```

## Usage

```bash
# lint the default workflows directory
ghalint

# lint a single file
ghalint lint .github/workflows/ci.yml

# strict mode
ghalint lint .github/workflows/ --strict

# json report
ghalint lint .github/workflows/ --json
```

## Project structure

```text
ghalint/
  ghalint/
    __init__.py
    models.py
    lint.py
    cli.py
    __main__.py
  tests/
    test_ghalint.py
  README.md
  pyproject.toml
```

## Repository

https://github.com/Axelgustavlindstrom/ghalint

## Tags / keywords

`github-actions`, `ci`, `lint`, `yaml`, `developer-tools`, `cli`
