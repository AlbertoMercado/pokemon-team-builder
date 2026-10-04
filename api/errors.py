"""Errors of the use cases and their HTTP status (docs/02-ddt/api.md, "Convenciones").

Services raise these exceptions without knowing about HTTP; ``register`` turns them into
``404``, ``409`` and ``422`` responses with FastAPI's usual body (``{"detail": ...}``).
"""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    """The resource does not exist: 404."""


class ConflictError(Exception):
    """The operation cannot be done in the current state: 409.

    With ``extra``, the body's ``detail`` is an object with the ``message`` and those fields
    (e.g. the data still to confirm before generating); without it, the message alone.
    """

    def __init__(self, message: str, extra: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.extra = extra


class InvalidValueError(Exception):
    """The request is well formed, but a value is not valid for what it changes: 422.

    For checks that need the data, such as a key battle's team with an unknown Pokémon; the
    rest are validated by the request schemas.
    """


type Handler = Callable[[Request, Exception], Awaitable[JSONResponse]]


def _handler(code: int) -> Handler:
    async def handle(request: Request, exc: Exception) -> JSONResponse:
        extra = exc.extra if isinstance(exc, ConflictError) else None
        detail: object = {"message": str(exc), **extra} if extra else str(exc)
        return JSONResponse({"detail": detail}, status_code=code)

    return handle


def register(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, _handler(status.HTTP_404_NOT_FOUND))
    app.add_exception_handler(ConflictError, _handler(status.HTTP_409_CONFLICT))
    app.add_exception_handler(InvalidValueError, _handler(status.HTTP_422_UNPROCESSABLE_CONTENT))
