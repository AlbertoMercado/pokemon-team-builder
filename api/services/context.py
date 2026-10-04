"""The engine's ``GameContext`` of a target game, built from both databases (RN-10, RN-18).

It has two parts (docs/02-ddt/plan-api.md, "Construcción del GameContext"):

- ``GameReference``: what reference.sqlite says about the game. Every form with its data in
  the game's generation, the type chart and the reviewable values as loaded, with their
  origin. ``GameReferences`` builds it on first use and keeps it in memory until the
  application restarts: reference data does not change while it runs.
- What the user has: favourites, rule settings, confirmations and the journey of the Hall of
  Fame, read on every request.
  ``build_context`` combines both.

A reviewable value is confirmed when the user confirmed it and the current load still
proposes what it proposed then. Otherwise it keeps its origin: the context uses an inferred
proposal as it is and treats a pending value as possible. Only suggestions can depend on such
values, and they are marked as unverified (CA-31): the API does not generate while a value
that takes part is unverified (``core.review.pending_facts``).
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from itertools import pairwise
from types import MappingProxyType

from sqlmodel import Session

from api.errors import NotFoundError
from api.repositories import reference as reference_repo
from core.domain import (
    Availability,
    Candidate,
    EvolutionStep,
    GameContext,
    GameInfo,
    HallOfFameEntry,
    KeyBattle,
    PokemonData,
    PoolEntry,
    Rival,
    Stage,
    TypeChart,
)
from core.review import Fact, FactKind, FactValue, FavoriteFacts, Origin
from core.rules.catalog import RuleSettings
from db import reference as ref_db
from db.user import ConfirmedValue, FactConfirmation, value_hash

type Confirmations = Mapping[str, FactConfirmation]


@dataclass(frozen=True)
class Reviewable:
    """A reviewable value as loaded: its proposal (or loaded value) and its origin (RN-18).

    ``subject`` is what it is about: the mechanic, the key battle or the form.
    """

    key: str
    kind: FactKind
    subject: str
    origin: Origin
    proposal: FactValue | None

    @property
    def proposal_hash(self) -> str:
        return value_hash(to_stored(self.proposal))

    def confirmation(self, confirmations: Confirmations) -> FactConfirmation | None:
        """The user's confirmation, if there is one and it answered the current proposal.

        An automatic value is never reviewed, so it ignores confirmations.
        """
        found = confirmations.get(self.key)
        if (
            found is None
            or self.origin is Origin.AUTOMATIC
            or found.proposed_value_hash != self.proposal_hash
        ):
            return None
        return found

    def fact(self, confirmations: Confirmations) -> Fact:
        """The value with the user's confirmation applied."""
        found = self.confirmation(confirmations)
        if found is None:
            return Fact(self.key, self.kind, self.origin, self.proposal)
        return Fact(self.key, self.kind, Origin.CONFIRMED, to_fact_value(found.confirmed_value))


def to_stored(value: FactValue | None) -> ConfirmedValue | None:
    """A value as user.sqlite keeps it: the Pokémon of a key battle as a list."""
    return list(value) if isinstance(value, tuple) else value


def to_fact_value(value: ConfirmedValue) -> FactValue:
    return tuple(value) if isinstance(value, list) else value


@dataclass(frozen=True)
class FormFacts:
    """Whether a form exists in the game and can arrive in time, as loaded (RN-03)."""

    exists: Reviewable
    arrival: Reviewable


@dataclass(frozen=True)
class LoadedBattle:
    """A key battle as loaded; its team is the value of ``fact`` (RN-17)."""

    slug: str
    category: str
    trainer: str
    fact: Reviewable


@dataclass(frozen=True)
class GameReference:
    """What reference.sqlite says about a target game, without the user's data.

    ``forms`` has every form with its data in the game's generation (RN-10): a form of a later
    generation keeps the types it appeared with and has no evolution steps, because RN-03
    discards it first. ``types`` are the types in the game's generation of every form that
    has them, to give a key battle's team corrected by the user its types.
    """

    slug: str
    name: str
    generation: int
    type_chart: TypeChart
    forms: Mapping[str, PokemonData]
    types: Mapping[str, tuple[str, ...]]
    availability: Mapping[str, FormFacts]
    mechanics: tuple[Reviewable, ...]
    key_battles: tuple[LoadedBattle, ...]

    def form_facts(self, pokemon: str) -> FormFacts:
        """A form without a row in the game does not exist there (automatic)."""
        found = self.availability.get(pokemon)
        if found is not None:
            return found
        prefix = f"pokemon:{self.slug}:{pokemon}"
        return FormFacts(
            Reviewable(f"{prefix}:exists", FactKind.EXISTS, pokemon, Origin.AUTOMATIC, False),
            Reviewable(f"{prefix}:arrival", FactKind.ARRIVAL, pokemon, Origin.AUTOMATIC, False),
        )

    @cached_property
    def _by_key(self) -> dict[str, Reviewable]:
        values = [*self.mechanics, *(battle.fact for battle in self.key_battles)]
        values += [v for facts in self.availability.values() for v in (facts.exists, facts.arrival)]
        return {value.key: value for value in values}

    def reviewable(self, key: str) -> Reviewable | None:
        """The value with ``key``, among the game's and those of every form."""
        return self._by_key.get(key)

    def game_facts(self, confirmations: Confirmations) -> list[Fact]:
        """The game's values: its mechanics, then its key battles in order."""
        values = [*self.mechanics, *(battle.fact for battle in self.key_battles)]
        return [value.fact(confirmations) for value in values]

    def favorite_facts(
        self, favorites: Iterable[str], confirmations: Confirmations
    ) -> list[FavoriteFacts]:
        """The availability values of each favourite that is a loaded form."""
        result = []
        for slug in favorites:
            if slug in self.forms:
                facts = self.form_facts(slug)
                result.append(
                    FavoriteFacts(
                        self.forms[slug],
                        facts.exists.fact(confirmations),
                        facts.arrival.fact(confirmations),
                    )
                )
        return result


class GameReferences:
    """The ``GameReference`` of each game, built on first use and kept until restart.

    After a data load the API has to be restarted (docs/04-manual-usuario/cargar-datos.md).
    """

    def __init__(self) -> None:
        self._games: dict[str, GameReference] = {}

    def get(self, reference: Session, game: str) -> GameReference:
        """``NotFoundError`` if ``game`` is not a target game."""
        found = self._games.get(game)
        if found is None:
            found = load_game_reference(reference, game)
            self._games[game] = found
        return found


def build_context(
    game: GameReference,
    favorites: Iterable[str],
    settings: RuleSettings,
    confirmations: Confirmations,
    journey: Sequence[HallOfFameEntry] = (),
) -> GameContext:
    """The engine's input: the game with the user's favourites, settings, confirmations and
    journey (RN-16).

    Favourites that are not loaded forms are left out. The pool has every other form of the
    game's generation or earlier, marked as unverified if a value of its own is (CA-31).
    """
    chosen = {slug for slug in favorites if slug in game.forms}
    candidates = []
    pool = []
    for slug, data in game.forms.items():
        if slug not in chosen and data.generation > game.generation:
            continue
        facts = game.form_facts(slug)
        exists = facts.exists.fact(confirmations)
        arrival = facts.arrival.fact(confirmations)
        availability = Availability(_possible(exists), _possible(arrival))
        if slug in chosen:
            candidates.append(Candidate(data, availability))
        else:
            pool.append(PoolEntry(data, availability, exists.is_known and arrival.is_known))
    mechanics = frozenset(
        value.subject for value in game.mechanics if value.fact(confirmations).value is True
    )
    return GameContext(
        game=GameInfo(game.slug, game.generation, mechanics),
        type_chart=game.type_chart,
        favorites=tuple(candidates),
        pool=tuple(pool),
        key_battles=_key_battles(game, confirmations),
        settings=settings,
        journey=tuple(journey),
    )


def _possible(fact: Fact) -> bool:
    """A yes/no value: the known one, an inferred proposal, or yes while pending."""
    return fact.value is not False


def _key_battles(game: GameReference, confirmations: Confirmations) -> tuple[KeyBattle, ...]:
    """The battles with a team, each rival with its types in the game; pending ones have none."""
    battles = []
    for battle in game.key_battles:
        team = battle.fact.fact(confirmations).value
        if not isinstance(team, tuple) or not team:
            continue
        rivals = tuple(Rival(pokemon, game.types[pokemon]) for pokemon in team)
        battles.append(KeyBattle(battle.slug, battle.category, battle.trainer, rivals))
    return tuple(battles)


# --- Loading a game from reference.sqlite -------------------------------------------------


def load_game_reference(reference: Session, slug: str) -> GameReference:
    """Reads everything the context of ``slug`` needs; ``NotFoundError`` if it is not a target."""
    game = reference_repo.target_game(reference, slug)
    if game is None:
        raise NotFoundError(f"El juego {slug} no existe o no se puede elegir como juego objetivo")
    generation = game.generation
    chart = TypeChart.from_hundredths(
        generation,
        [t.slug for t in reference_repo.types_until(reference, generation)],
        {
            (e.attacking, e.defending): e.factor
            for e in reference_repo.type_efficacies(reference, generation)
        },
    )
    forms = _FormBuilder(reference, generation, game.version_group).build()
    types = {slug: data.types for slug, data in forms.items() if data.generation <= generation}
    return GameReference(
        slug=game.slug,
        name=game.name_es,
        generation=generation,
        type_chart=chart,
        forms=MappingProxyType(forms),
        types=MappingProxyType(types),
        availability=MappingProxyType(_availability(reference, slug)),
        mechanics=tuple(
            Reviewable(row.fact_key, FactKind.MECHANIC, row.mechanic, Origin(row.origin), row.value)
            for row in reference_repo.game_mechanics(reference, slug)
        ),
        key_battles=_loaded_battles(reference, slug),
    )


def _availability(reference: Session, game: str) -> dict[str, FormFacts]:
    result = {}
    for row in reference_repo.game_pokemon(reference, game):
        prefix = f"pokemon:{game}:{row.pokemon}"
        result[row.pokemon] = FormFacts(
            Reviewable(
                f"{prefix}:exists",
                FactKind.EXISTS,
                row.pokemon,
                Origin(row.exists_origin),
                row.exists_in_game,
            ),
            Reviewable(
                f"{prefix}:arrival",
                FactKind.ARRIVAL,
                row.pokemon,
                Origin(row.arrival_origin),
                row.can_arrive,
            ),
        )
    return result


def _loaded_battles(reference: Session, game: str) -> tuple[LoadedBattle, ...]:
    teams: dict[str, list[str]] = defaultdict(list)
    for row in reference_repo.key_battle_pokemon(reference, game):
        teams[row.battle].append(row.pokemon)
    battles = []
    for battle in reference_repo.key_battles(reference, game):
        origin = Origin(battle.origin)
        team = tuple(teams[battle.slug]) if origin is not Origin.PENDING else None
        fact = Reviewable(battle.fact_key, FactKind.KEY_BATTLE, battle.slug, origin, team)
        battles.append(LoadedBattle(battle.slug, str(battle.category), battle.trainer_name, fact))
    return tuple(battles)


class _FormBuilder:
    """Builds the ``PokemonData`` of every form in a game (RN-05, RN-09, RN-10, RN-11)."""

    def __init__(self, reference: Session, generation: int, version_group: str) -> None:
        self.generation = generation
        self.species = {s.slug: s for s in reference_repo.all_species(reference)}
        self.forms = list(reference_repo.all_forms(reference))
        self.default_form = {f.species: f.slug for f in self.forms if f.is_default}
        self.species_of = {f.slug: f.species for f in self.forms}
        self.types: dict[str, dict[int, list[str]]] = defaultdict(lambda: defaultdict(list))
        for form_type in reference_repo.all_form_types(reference):
            self.types[form_type.pokemon][form_type.generation].append(form_type.type)
        self.egg_groups: dict[int, set[str]] = defaultdict(set)
        for egg_group in reference_repo.all_egg_groups(reference):
            chain = self.species[egg_group.species].evolution_chain
            self.egg_groups[chain].add(egg_group.egg_group)
        self.steps: dict[tuple[str, str], list[ref_db.EvolutionStep]] = defaultdict(list)
        self.steps_into: dict[str, list[ref_db.EvolutionStep]] = defaultdict(list)
        for step in reference_repo.evolution_steps(reference, version_group):
            self.steps[(step.from_pokemon, step.to_pokemon)].append(step)
            self.steps_into[step.to_pokemon].append(step)

    def build(self) -> dict[str, PokemonData]:
        result = {}
        for form in self.forms:
            types = self._types(form.slug)
            if types:
                result[form.slug] = self._pokemon(form, types)
        return result

    def _types(self, pokemon: str) -> tuple[str, ...]:
        """Its types in the game's generation or, if it appeared later, the first it had."""
        by_generation = self.types.get(pokemon, {})
        if self.generation in by_generation:
            return tuple(by_generation[self.generation])
        later = [g for g in by_generation if g > self.generation]
        return tuple(by_generation[min(later)]) if later else ()

    def _pokemon(self, form: ref_db.Pokemon, types: tuple[str, ...]) -> PokemonData:
        species = self.species[form.species]
        stages = self._stages(form, species)
        steps = [
            EvolutionStep(
                row.from_pokemon, row.to_pokemon, row.trigger, tuple(row.conditions.items())
            )
            for a, b in pairwise(stages)
            for row in self.steps[(a.pokemon, b.pokemon)]
        ]
        return PokemonData(
            slug=form.slug,
            species=species.slug,
            dex_number=species.dex_number,
            name=form.name_es,
            generation=species.generation,
            types=types,
            evolution_chain=species.evolution_chain,
            stages=tuple(stages),
            line_egg_groups=frozenset(self.egg_groups[species.evolution_chain]),
            evolution_steps=tuple(steps),
            region=form.region,
            is_legendary=species.is_legendary,
            is_mythical=species.is_mythical,
        )

    def _stages(self, form: ref_db.Pokemon, species: ref_db.Species) -> list[Stage]:
        """From the first stage of the line that exists in the game's generation to ``form``.

        A pre-evolution of a later generation does not exist yet (Snorlax hatches as itself
        before Munchlax). The form of each earlier stage is the one the evolution steps come
        from (a regional line stays regional), or the species' default form.
        """
        stages = [_stage(form.slug, species)]
        if species.generation > self.generation:
            return stages
        current, current_species = form.slug, species
        while current_species.evolves_from is not None:
            previous = self.species[current_species.evolves_from]
            if previous.generation > self.generation:
                break
            sources = [
                step.from_pokemon
                for step in self.steps_into[current]
                if self.species_of.get(step.from_pokemon) == previous.slug
            ]
            current = sources[0] if sources else self.default_form[previous.slug]
            current_species = previous
            stages.insert(0, _stage(current, previous))
        return stages


def _stage(pokemon: str, species: ref_db.Species) -> Stage:
    return Stage(pokemon, species.slug, species.is_baby, species.requires_incense)
