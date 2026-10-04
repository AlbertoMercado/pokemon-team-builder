"""Build the WikiDex pages used by the ingest tests.

Usage (from the repository root, with the pages cached by a real load; PYTHONPATH=. is needed
because the project is not installed as a package):

    PYTHONPATH=. uv run python tests/ingest/fixtures/wikidex/extract_wikidex.py \
        <data-dir>/cache/wikidex

Team pages are cut down to their FireRed and LeafGreen section, so the repository keeps only
the minimum WikiDex content the tests need. See the README next to this script.
"""

import sys
from pathlib import Path

from ingest.sources.wikidex.fetch import PageCache
from ingest.sources.wikidex.parse import find_section

OUTPUT = Path(__file__).resolve().parent
SECTION = "Pokémon Rojo Fuego y Pokémon Verde Hoja"
TEAM_PAGES = ("Brock", "Giovanni", "Azul (personaje)")
WHOLE_PAGES = ("Bruno",)  # disambiguation page, kept whole (it is short)


def main(cache_dir: Path) -> None:
    source = PageCache(cache_dir, fetcher=None)
    target = PageCache(OUTPUT, fetcher=None)
    for title in (*TEAM_PAGES, *WHOLE_PAGES):
        page = source.page(title)
        if title in TEAM_PAGES:
            page = page.model_copy(update={"wikitext": find_section(page.wikitext, SECTION)})
        target.path(title).write_text(page.model_dump_json(indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
