"""The compiled web (``web/dist``) served by the API at ``/``: one process for both
(docs/02-ddt/arquitectura.md, "Despliegue").

The files of the build are served as they are. Any other ``GET`` outside ``/api`` gets
``index.html``, so the routes of the web (``/pokemon/vulpix``, ``/juego/firered/resultado``)
also work when they are reloaded or linked. Paths under ``/api`` are never covered: an unknown
one keeps answering ``404`` in JSON.
"""

from pathlib import Path

from fastapi import FastAPI, status
from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

INDEX = "index.html"


def _is_api(path: str) -> bool:
    return path == "api" or path.startswith("api/")


class WebFiles(StaticFiles):
    """Static files with a fallback to ``index.html`` for the routes of the web."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as error:
            if error.status_code != status.HTTP_404_NOT_FOUND or _is_api(path):
                raise
            return await super().get_response(INDEX, scope)


def mount_web(app: FastAPI, web_dir: Path | None) -> bool:
    """Serves ``web_dir`` at ``/`` after the API routes, if it has a build of the web.

    Without one (``web_dir`` is ``None`` or has no ``index.html``), only the API is served.
    """
    if web_dir is None or not (web_dir / INDEX).is_file():
        return False
    app.mount("/", WebFiles(directory=web_dir, html=True), name="web")
    return True
