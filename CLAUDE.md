# CLAUDE.md

`xdrgen` is a CLI tool that generates production-like Defender XDR telemetry based on the official Defender XDR table definitions.

## Overview

* Tests: `tests/`
* Telemetry Models: `models/`
* Telemetry Generators: `generators/`

## Workflow

Formatting:

```bash
uv run ruff format .
```

Linting (with automatic fixes):

```bash
uv run ruff check --fix .
```

Tests:

```bash
uv run pytest -q
```

## Generic Rules

* Make sure to always write unit tests in the tests folder for new features
* Make sure to always update the README.md with changes for the end user
* All telemetry generators should produce production worthy data, not just random fake values. Consult the microsoft documentation if you are not sure what value a field should have
* Keep comments short and to the point
* Do not add redundant section devider comments
* Always format Python source
* Always lint Python source with `ruff check --fix` to auto-apply safe fixes
* Always update the `generate --help` output in README.md if something changes in the CLI