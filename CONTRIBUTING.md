# Contributing to Axiom

Thanks for helping improve Axiom. Treat the published JSON Schema and its
conformance behavior as the public contract; changes to either require tests
and a documented versioning decision.

## Development

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/pytest -q
.venv/bin/ruff check src tests examples
```

CI covers Python 3.10 through 3.13. Add positive and negative contract
fixtures for schema changes, and keep generated Python/TypeScript output
deterministic. Update the README or `CHANGELOG.md` for CLI, schema, or
compatibility changes.

Do not commit caches, wheels, `__pycache__`, generated reports, or private robot
contracts. Pull requests should explain whether a change is normative schema,
semantic validation, lint guidance, or tooling behavior.
