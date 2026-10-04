"""GET /api/meta: versions of the application and of the data."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from api.database import reference_session
from api.schemas.meta import Meta
from api.services import meta as service

router = APIRouter(tags=["Metadatos"])


@router.get("/meta", summary="Versión de la aplicación y de los datos")
def get_meta(reference: Annotated[Session, Depends(reference_session)]) -> Meta:
    """Versión de la aplicación y de la carga de datos con la que trabaja (commit de PokeAPI,
    fecha y juegos). `503` si todavía no se han cargado los datos."""
    return service.meta(reference)
