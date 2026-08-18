"""Allow ``python -m axiom`` to behave like the installed CLI."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
