"""Errors of the use cases and their HTTP status (docs/02-ddt/api.md, "Convenciones").

Services raise these exceptions without knowing about HTTP; ``register`` turns them into
``404`` and ``409`` responses with FastAPI's usual body (``{"detail": ...}``).
"""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    """The resource does not exist: 404."""


class ConflictError(Exception):
    """The operation cannot be done in the current state: 409."""


type Handler = Callable[[Request, Exception], Awaitable[JSONResponse]]


def _handler(code: int) -> Handler:
    async def handle(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=code)

    return handle


def register(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, _handler(status.HTTP_404_NOT_FOUND))
    app.add_exception_handler(ConflictError, _handler(status.HTTP_409_CONFLICT))
