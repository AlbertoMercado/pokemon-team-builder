"""Architecture guard: core/ imports only the standard library (ADR-0002).

import-linter checks the dependencies between project packages (pyproject.toml), but it can
only forbid packages listed by name. This test covers the general case: any import in core/
that is neither the standard library nor core itself fails, whatever library it is.
"""

import ast
import sys
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent.parent / "core"
ALLOWED_TOP_LEVEL = sys.stdlib_module_names | {"core"}


def _imported_top_levels(path: Path) -> set[str]:
    """Return the top-level names of the absolute imports in a Python file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_core_imports_only_standard_library() -> None:
    offenders = sorted(
        f"{path.relative_to(CORE_DIR.parent)}: {name}"
        for path in CORE_DIR.rglob("*.py")
        for name in _imported_top_levels(path) - ALLOWED_TOP_LEVEL
    )
    assert not offenders, f"core/ must only import the standard library: {offenders}"


def test_guard_detects_third_party_import(tmp_path: Path) -> None:
    """The guard itself works: a third-party import is reported."""
    module = tmp_path / "module.py"
    module.write_text("import os\nfrom pydantic import BaseModel\nfrom . import sibling\n")
    assert _imported_top_levels(module) - ALLOWED_TOP_LEVEL == {"pydantic"}
