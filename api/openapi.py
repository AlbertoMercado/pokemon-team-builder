"""Exports the OpenAPI contract of the API without starting it.

    uv run python -m api.openapi [FILE]

Writes the contract as JSON to ``FILE`` (creating its directory) or to the standard output.
The web generates its typed client from it with ``npm run api:generate`` (ADR-0007,
docs/02-ddt/plan-web.md). Building the contract does not open any database.
"""

import json
import sys
from pathlib import Path

from api.main import create_app


def contract() -> str:
    """The OpenAPI contract as JSON, always the same for the same code."""
    return json.dumps(create_app().openapi(), ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str]) -> None:
    text = contract()
    if not argv:
        sys.stdout.write(text)
        return
    path = Path(argv[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
