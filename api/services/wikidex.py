"""Links to the WikiDex pages the loaded data comes from (ADR-0004, ADR-0011).

The covers of the games are fair use only in the WikiDex articles, so each one links to the page
of its file (RF-18, CA-56). The teams of the key battles are CC BY-NC-SA, so each one links to
the revision of the page it was read from. The API only builds the links: it never asks WikiDex.
"""

from urllib.parse import quote, urlencode

WIKIDEX_URL = "https://www.wikidex.net"


def page_url(title: str) -> str:
    """The URL of a WikiDex page, such as ``Archivo:Carátula de Rojo Fuego.png``."""
    return f"{WIKIDEX_URL}/wiki/{quote(title.replace(' ', '_'), safe=':/')}"


def revision_url(title: str, revision: int) -> str:
    """The URL of the revision ``revision`` of a WikiDex page."""
    query = urlencode({"title": title.replace(" ", "_"), "oldid": revision})
    return f"{WIKIDEX_URL}/index.php?{query}"
