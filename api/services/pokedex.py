"""The Pokédex of the completed games: progress, initial list, objective, ways of obtaining
and the user's marks (RF-20 to RF-24).

Each game recorded in the Hall of Fame has its Pokédex (CA-68). ``_context`` adds to its
``PokedexReference`` the user's marks and those of the other completed games that can send
Pokémon to it (RN-25), and ``core.pokedex`` applies the rules. Marks of species that a new
load no longer has in the Pokédex are ignored.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from sqlmodel import Session

from api.errors import ConflictError, InvalidValueError, NotFoundError
from api.repositories import reference as reference_repo
from api.repositories import user as user_repo
from api.schemas.pokedex import (
    DexEvolutionOut,
    InitialListIn,
    ObjectiveOut,
    ObtentionMethodOut,
    PokedexGameOut,
    PokedexMarkIn,
    PokedexOut,
    PokedexPokemonOut,
    PokedexProgressOut,
    PokedexSpeciesOut,
    SpeciesRefOut,
    WayOut,
)
from api.services import hall_of_fame
from api.services.images import artwork_url, cover_url, image_url
from api.services.pokedex_reference import Names, PokedexReference, PokedexReferences
from core.pokedex import (
    InGameWay,
    ObtentionMethod,
    PokedexContext,
    TransferSource,
    impossible_species,
    objective,
    obtention_methods,
    progress,
)
from db.user import DexStatus, PokedexEntry


@dataclass(frozen=True)
class PokedexData:
    """Where the Pokédex comes from: both databases and the cache of reference data."""

    user: Session
    reference: Session
    references: PokedexReferences

    @property
    def names(self) -> Names:
        return self.references.names(self.reference)


@dataclass(frozen=True)
class _Pokedex:
    """A completed game's Pokédex: its reference, Hall of Fame entry, marks and context."""

    reference: PokedexReference
    entry: int
    marks: dict[str, PokedexEntry]
    context: PokedexContext


def list_pokedexes(data: PokedexData) -> list[PokedexGameOut]:
    """The completed games in journey order, each with its progress (RF-20). Games no
    longer loaded are left out."""
    loaded = reference_repo.all_games(data.reference)
    result = []
    for entry in hall_of_fame.list_entries(data.user, data.reference):
        if entry.game not in loaded:
            continue
        dex = _load(data, entry.game)
        result.append(
            PokedexGameOut(
                game=entry.game,
                game_name=dex.reference.name,
                cover_url=cover_url(entry.game, dex.reference.has_cover),
                hall_of_fame_entry=dex.entry,
                progress=_progress(dex.context),
            )
        )
    return result


def get_pokedex(data: PokedexData, game: str) -> PokedexOut:
    """Every species of the Pokédex with its marks (RF-21, RF-24)."""
    dex = _load(data, game)
    automatic = impossible_species(dex.context) - dex.context.impossible
    return PokedexOut(
        game=game,
        game_name=dex.reference.name,
        hall_of_fame_entry=dex.entry,
        progress=_progress(dex.context),
        species=[_species(dex, s.species, automatic) for s in dex.context.species],
    )


def start_pokedex(
    data: PokedexData,
    game: str,
    body: InitialListIn,
) -> PokedexOut:
    """Confirms the initial list (RF-21); ``409`` if it was already confirmed."""
    dex = _load(data, game)
    if dex.context.started:
        raise ConflictError(
            f"La lista inicial de {dex.reference.name} ya está confirmada: corrige los "
            "registrados en el detalle"
        )
    _check_species(dex, body.registered)
    user_repo.start_pokedex(data.user, dex.entry, body.registered)
    return get_pokedex(data, game)


def get_objective(
    data: PokedexData,
    game: str,
    skipped: Iterable[str],
) -> ObjectiveOut:
    """The card of the first species neither registered, impossible nor skipped (RN-23)."""
    dex = _load(data, game)
    found = objective(dex.context, frozenset(skipped))
    if found is None:
        return ObjectiveOut(pokemon=None)
    return ObjectiveOut(pokemon=_card(dex, found, data.names))


def get_pokemon(data: PokedexData, game: str, species: str) -> PokedexPokemonOut:
    """The card of ``species`` with every way of obtaining it (RF-22, RF-23)."""
    dex = _load(data, game)
    _check_species(dex, [species], NotFoundError)
    return _card(dex, species, data.names)


def mark_pokemon(
    data: PokedexData,
    game: str,
    species: str,
    change: PokedexMarkIn,
) -> PokedexPokemonOut:
    """Registers it, marks it as impossible or unmarks it, and chooses its way (RF-22 to
    RF-24). Only the fields given change."""
    dex = _load(data, game)
    _check_species(dex, [species], NotFoundError)
    _check_started(dex)
    current = dex.marks.get(species)
    status = current.status if current else None
    chosen = current.chosen_method if current else None
    fields = change.model_fields_set
    if "status" in fields:
        status = DexStatus(change.status) if change.status else None
    if "chosen_method" in fields:
        chosen = change.chosen_method
        keys = [m.key for m in obtention_methods(dex.context, species).methods]
        if chosen is not None and chosen not in keys:
            raise InvalidValueError(f"{chosen} no es una forma de obtener {species}")
    user_repo.save_pokedex_mark(data.user, dex.entry, species, status, chosen)
    return get_pokemon(data, game, species)


def unmark_pokemon(data: PokedexData, game: str, species: str) -> None:
    """Removes its mark and its chosen way (RF-24)."""
    dex = _load(data, game)
    _check_species(dex, [species], NotFoundError)
    _check_started(dex)
    user_repo.save_pokedex_mark(data.user, dex.entry, species, None, None)


# --- Building the context ----------------------------------------------------------------


def _load(data: PokedexData, game: str) -> _Pokedex:
    """The Pokédex of ``game``: ``404`` if it is not in the Hall of Fame or not loaded."""
    completed = user_repo.completed_games(data.user)
    entry = completed.get(game)
    if entry is None:
        raise NotFoundError(f"El juego {game} no está en el Hall of Fame: no tiene Pokédex")
    own = data.references.get(data.reference, game)
    started = user_repo.started_pokedexes(data.user)
    marks = user_repo.pokedex_marks(data.user)
    sources = []
    for source_game, limit in own.transfers:
        source = data.references.get(data.reference, source_game)
        source_entry = completed.get(source_game)
        sources.append(
            TransferSource(
                game=source_game,
                completed=source_entry is not None,
                registered=_with(marks.get(source_entry or 0, {}), DexStatus.REGISTERED),
                encounters=source.encounters,
                max_species_generation=limit,
                starters=source.starters,
            )
        )
    in_dex = {s.species for s in own.species}
    mine = {s: mark for s, mark in marks.get(entry, {}).items() if s in in_dex}
    context = PokedexContext(
        game=own.game(user_repo.confirmations(data.user, game)),
        has_breeding=own.has_breeding,
        species=own.species,
        registered=_with(mine, DexStatus.REGISTERED),
        impossible=_with(mine, DexStatus.IMPOSSIBLE),
        started=entry in started,
        sources=tuple(sources),
        starters=own.starters,
    )
    return _Pokedex(own, entry, mine, context)


def _with(marks: dict[str, PokedexEntry], status: DexStatus) -> frozenset[str]:
    return frozenset(s for s, mark in marks.items() if mark.status is status)


def _check_species(
    dex: _Pokedex, species: Iterable[str], error: type[Exception] = InvalidValueError
) -> None:
    unknown = sorted(set(species) - set(dex.reference.info))
    if unknown:
        raise error(f"No están en la Pokédex de {dex.reference.name}: {', '.join(unknown)}")


def _check_started(dex: _Pokedex) -> None:
    if not dex.context.started:
        raise ConflictError(
            f"Confirma antes la lista inicial de la Pokédex de {dex.reference.name} (RF-21)"
        )


# --- Responses ---------------------------------------------------------------------------


def _progress(context: PokedexContext) -> PokedexProgressOut:
    found = progress(context)
    return PokedexProgressOut(
        registered=found.registered,
        total=found.total,
        impossible=found.impossible,
        percent=found.percent,
        status=found.status,
    )


def _species_fields(dex: _Pokedex, species: str, automatic: bool) -> dict[str, object]:
    info = dex.reference.info[species]
    mark = dex.marks.get(species)
    return {
        "species": species,
        "number": info.number,
        "name": info.name,
        "pokemon": info.pokemon,
        "types": list(info.types),
        "image_url": image_url(info.pokemon, info.has_image),
        "status": mark.status if mark else None,
        "automatically_impossible": automatic,
    }


def _species(
    dex: _Pokedex, species: str, automatic: set[str] | frozenset[str]
) -> PokedexSpeciesOut:
    return PokedexSpeciesOut.model_validate(_species_fields(dex, species, species in automatic))


def _card(dex: _Pokedex, species: str, names: Names) -> PokedexPokemonOut:
    found = obtention_methods(dex.context, species)
    mark = dex.marks.get(species)
    keys = [m.key for m in found.methods]
    chosen = mark.chosen_method if mark and mark.chosen_method in keys else None
    info = dex.reference.info[species]
    return PokedexPokemonOut.model_validate(
        {
            **_species_fields(dex, species, found.automatically_impossible),
            "artwork_url": artwork_url(info.pokemon, info.has_artwork),
            "chosen_method": chosen,
            "methods": [
                _method(m, index == 0, m.key == chosen, names)
                for index, m in enumerate(found.methods)
            ],
        }
    )


def _method(
    method: ObtentionMethod, recommended: bool, chosen: bool, names: Names
) -> ObtentionMethodOut:
    step = method.evolution
    return ObtentionMethodOut(
        key=method.key,
        kind=method.kind,
        recommended=recommended,
        chosen=chosen,
        way=_way(method.way, names) if method.way else None,
        game=method.game,
        game_name=names.games.get(method.game, method.game) if method.game else None,
        pokemon=method.pokemon,
        pokemon_name=names.species.get(method.pokemon, method.pokemon) if method.pokemon else None,
        pokemon_registered=method.pokemon_registered,
        evolution=DexEvolutionOut(trigger=step.trigger, conditions=dict(step.conditions))
        if step
        else None,
        incense=method.incense,
    )


def _way(way: InGameWay, names: Names) -> WayOut:
    return WayOut(
        kind=way.kind,
        location=way.location,
        location_name=names.locations.get(way.location, way.location),
        area=way.area,
        method=way.method,
        rarity=way.rarity,
        times=list(way.times),
        choice=way.choice,
        item=way.item,
        conditions=list(way.conditions),
        alternatives=[
            SpeciesRefOut(species=s, name=names.species.get(s, s)) for s in way.alternatives
        ],
    )
