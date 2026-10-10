"""What reference.sqlite says about the Pokédex of a game, for ``core.pokedex`` (RN-22 to RN-26).

``PokedexReferences`` reads it on first use and keeps it until the application restarts, like
``GameReferences``: reference data does not change while it runs. The Pokédex registers
species, so the forms of the encounters, the event Pokémon and the evolution steps become
their species (``deoxys-normal`` is ``deoxys``). The user's marks are added by
``api.services.pokedex``.

The starters of each game are loaded as the form of their final evolution (RN-21); the
Pokédex needs the species received, the first stage of the line in the game's generation:
Pikachu in Yellow, not Pichu (CA-87).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from sqlmodel import Session

from api.errors import NotFoundError
from api.repositories import reference as reference_repo
from api.services.context import Confirmations, Reviewable
from core.domain import CONTESTS, DAY_NIGHT_CYCLE, EvolutionStep, GameInfo
from core.pokedex import DexSpecies, Encounter
from core.review import FactKind, Origin
from db import reference as ref_db

MECHANICS = (CONTESTS, DAY_NIGHT_CYCLE)


@dataclass(frozen=True)
class SpeciesInfo:
    """How a species of the Pokédex is shown: its number there, name and base form."""

    number: int
    name: str
    pokemon: str
    types: tuple[str, ...]
    has_image: bool
    has_artwork: bool


@dataclass(frozen=True)
class PokedexReference:
    """The Pokédex of a loaded game, without the user's marks.

    ``species`` are numbered by their position, so several Pokédexes keep one order; ``info``
    has the number shown. ``encounters`` are by species, to transfer from this game (RN-25).
    ``transfers`` are the games that can send Pokémon to this one, with their generation
    limit. ``mechanics`` are the reviewable mechanics as loaded (RN-18).
    """

    slug: str
    name: str
    generation: int
    has_breeding: bool
    has_cover: bool
    mechanics: tuple[Reviewable, ...]
    species: tuple[DexSpecies, ...]
    info: Mapping[str, SpeciesInfo]
    encounters: Mapping[str, tuple[Encounter, ...]]
    starters: frozenset[str]
    transfers: tuple[tuple[str, int | None], ...]

    def game(self, confirmations: Confirmations) -> GameInfo:
        """The game with its mechanics. One not loaded, or pending, counts as present: better
        to propose an evolution the game may not allow than to hide one it does."""
        loaded = {value.subject: value for value in self.mechanics}
        mechanics = frozenset(
            m
            for m in MECHANICS
            if m not in loaded or loaded[m].fact(confirmations).value is not False
        )
        return GameInfo(self.slug, self.generation, mechanics, self.name)


@dataclass(frozen=True)
class Names:
    """Spanish names of every species, place and game, to show the ways of obtaining."""

    species: Mapping[str, str]
    locations: Mapping[str, str]
    games: Mapping[str, str]


class PokedexReferences:
    """The ``PokedexReference`` of each game and the names, read on first use."""

    def __init__(self) -> None:
        self._games: dict[str, PokedexReference] = {}
        self._names: Names | None = None

    def get(self, reference: Session, game: str) -> PokedexReference:
        """``NotFoundError`` if ``game`` is not loaded."""
        found = self._games.get(game)
        if found is None:
            found = load_pokedex_reference(reference, game)
            self._games[game] = found
        return found

    def names(self, reference: Session) -> Names:
        if self._names is None:
            self._names = Names(
                species=MappingProxyType(
                    {s.slug: s.name_es for s in reference_repo.all_species(reference)}
                ),
                locations=MappingProxyType(
                    {
                        place.slug: place.name_es or place.name_en or place.slug
                        for place in reference_repo.all_locations(reference)
                    }
                ),
                games=MappingProxyType(
                    {g.slug: g.name_es for g in reference_repo.all_games(reference).values()}
                ),
            )
        return self._names


def load_pokedex_reference(reference: Session, slug: str) -> PokedexReference:
    game = reference_repo.all_games(reference).get(slug)
    if game is None:
        raise NotFoundError(f"El juego {slug} no está en los datos cargados")
    species = {s.slug: s for s in reference_repo.all_species(reference)}
    forms = reference_repo.all_forms(reference)
    form_species = {form.slug: form.species for form in forms}
    defaults = {form.species: form for form in forms if form.is_default}
    numbers = reference_repo.pokedex_numbers(reference, slug)
    in_dex = {s for s, _ in numbers}
    types = reference_repo.types_in_generation(
        reference, [defaults[s].slug for s in in_dex], game.generation
    )
    egg_groups: dict[str, set[str]] = {}
    for row in reference_repo.all_egg_groups(reference):
        egg_groups.setdefault(row.species, set()).add(row.egg_group)
    encounters = _encounters(reference, slug, form_species)
    evolutions = _evolutions(reference, game.version_group, defaults, in_dex)
    events = {form_species[p] for p in reference_repo.event_pokemon(reference, slug)}
    dex = tuple(
        DexSpecies(
            species=s,
            number=position,
            generation=species[s].generation,
            egg_groups=frozenset(egg_groups.get(s, ())),
            requires_incense=species[s].requires_incense,
            evolutions=evolutions.get(s, ()),
            encounters=encounters.get(s, ()),
            is_event=s in events,
        )
        for position, (s, _) in enumerate(numbers, start=1)
    )
    info = {
        s: SpeciesInfo(
            number,
            species[s].name_es,
            defaults[s].slug,
            types.get(defaults[s].slug, ()),
            defaults[s].image is not None,
            defaults[s].artwork is not None,
        )
        for s, number in numbers
    }
    return PokedexReference(
        slug=game.slug,
        name=game.name_es,
        generation=game.generation,
        has_breeding=game.has_breeding,
        has_cover=game.cover is not None,
        mechanics=tuple(
            Reviewable(row.fact_key, FactKind.MECHANIC, row.mechanic, Origin(row.origin), row.value)
            for row in reference_repo.game_mechanics(reference, slug)
        ),
        species=dex,
        info=MappingProxyType(info),
        encounters=MappingProxyType(encounters),
        starters=_starters(reference, game, species, form_species),
        transfers=tuple(
            (source.slug, limit) for source, limit in reference_repo.transfers_to(reference, slug)
        ),
    )


def _encounters(
    reference: Session, game: str, form_species: Mapping[str, str]
) -> dict[str, tuple[Encounter, ...]]:
    found: dict[str, list[Encounter]] = {}
    for row, place in reference_repo.encounters(reference, game):
        found.setdefault(form_species[row.pokemon], []).append(
            Encounter(
                row.location,
                row.method,
                row.rarity,
                tuple(row.conditions),
                row.area,
                place.event_item,
            )
        )
    return {s: tuple(rows) for s, rows in found.items()}


def _evolutions(
    reference: Session,
    version_group: str,
    defaults: Mapping[str, ref_db.Pokemon],
    in_dex: set[str],
) -> dict[str, tuple[EvolutionStep, ...]]:
    """The steps between base forms of species of the Pokédex, by the species they lead to."""
    species_of = {form.slug: s for s, form in defaults.items()}
    found: dict[str, list[EvolutionStep]] = {}
    for step in reference_repo.evolution_steps(reference, version_group):
        origin, target = species_of.get(step.from_pokemon), species_of.get(step.to_pokemon)
        if origin in in_dex and target in in_dex:
            found.setdefault(target, []).append(
                EvolutionStep(origin, target, step.trigger, tuple(step.conditions.items()))
            )
    return {s: tuple(steps) for s, steps in found.items()}


def _starters(
    reference: Session,
    game: ref_db.Game,
    species: Mapping[str, ref_db.Species],
    form_species: Mapping[str, str],
) -> frozenset[str]:
    """The species received as starter: the first stage of each line in the game's
    generation (CA-87)."""
    result = set()
    for form in reference_repo.game_starters(reference, game.slug):
        current = species[form_species[form]]
        while current.evolves_from is not None:
            previous = species[current.evolves_from]
            if previous.generation > game.generation:
                break
            current = previous
        result.add(current.slug)
    return frozenset(result)
