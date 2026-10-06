"""Transformation of validated PokeAPI rows into reference.sqlite rows.

Pure functions: no files, no network. Every rule applied here is described in the data load
plan (docs/02-ddt/plan-carga-datos.md), section "Revisión del volcado de PokeAPI".
"""

from collections import defaultdict
from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from db.reference import (
    EvolutionStep,
    Game,
    GamePokemon,
    Generation,
    Origin,
    Pokemon,
    PokemonType,
    ReferenceModel,
    Species,
    SpeciesEggGroup,
    Type,
    TypeEfficacy,
    VersionGroup,
)
from db.reference.evolution import ConditionValue
from ingest import scope
from ingest.sources.curated import CuratedData
from ingest.sources.pokeapi.rows import (
    DexNumberRow,
    EggGroupRow,
    EvolutionRow,
    GenerationRow,
    IdentifierRow,
    PokedexRow,
    PokemonFormRow,
    PokemonRow,
    PokemonTypePastRow,
    PokemonTypeRow,
    SpeciesEggGroupRow,
    SpeciesNameRow,
    SpeciesRow,
    TypeEfficacyPastRow,
    TypeEfficacyRow,
    TypeNameRow,
    TypeRow,
    VersionGroupRow,
    VersionNameRow,
    VersionRow,
)

SPANISH_LANGUAGE_ID = 7

# PokeAPI ids from 10000 on are special types (``unknown``, ``shadow``), not real ones.
FIRST_SPECIAL_TYPE_ID = 10000

# Evolution columns that identify the row, not a condition.
EVOLUTION_ROW_KEYS = frozenset(
    {"id", "evolved_species_id", "evolution_trigger_id", "version_group_id", "is_default"}
)
# Yes/no conditions: ``False`` means the condition does not apply.
FLAG_CONDITIONS = frozenset(
    {"needs_overworld_rain", "turn_upside_down", "needs_multiplayer", "near_special_rock"}
)
# Form columns: they only say which form evolves, which is the default one for loaded rows.
FORM_COLUMNS = frozenset({"required_pokemon_form_id", "evolved_pokemon_form_id"})


class TransformError(Exception):
    """The PokeAPI data is not consistent with what the load expects."""


@dataclass(frozen=True)
class PokeapiTables:
    """Every PokeAPI file the load reads, already validated."""

    generations: list[GenerationRow]
    version_groups: list[VersionGroupRow]
    versions: list[VersionRow]
    version_names: list[VersionNameRow]
    types: list[TypeRow]
    type_names: list[TypeNameRow]
    type_efficacy: list[TypeEfficacyRow]
    type_efficacy_past: list[TypeEfficacyPastRow]
    species: list[SpeciesRow]
    species_names: list[SpeciesNameRow]
    pokemon: list[PokemonRow]
    pokemon_forms: list[PokemonFormRow]
    pokemon_types: list[PokemonTypeRow]
    pokemon_types_past: list[PokemonTypePastRow]
    egg_groups: list[EggGroupRow]
    species_egg_groups: list[SpeciesEggGroupRow]
    evolutions: list[EvolutionRow]
    evolution_triggers: list[IdentifierRow]
    items: list[IdentifierRow]
    locations: list[IdentifierRow]
    moves: list[IdentifierRow]
    regions: list[IdentifierRow]
    pokedexes: list[PokedexRow]
    dex_numbers: list[DexNumberRow]


def build_rows(tables: PokeapiTables, curated: CuratedData) -> list[ReferenceModel]:
    """Every reference.sqlite row that comes from PokeAPI, for the generations in scope.

    ``curated`` provides the incense babies (CA-36) and the arrival rules (CA-28).
    """
    return list(_Builder(tables, curated).rows())


def _lookup[K, V](mapping: Mapping[K, V], key: K, what: str) -> V:
    try:
        return mapping[key]
    except KeyError:
        raise TransformError(f"{what} {key} no existe en PokeAPI") from None


class _Builder:
    def __init__(self, tables: PokeapiTables, curated: CuratedData) -> None:
        self.t = tables
        self.curated = curated
        self.incense_babies = set(curated.breeding.incense_babies)
        self.generations = [g for g in tables.generations if g.id <= scope.MAX_GENERATION]
        self.all_version_groups = {vg.id: vg for vg in tables.version_groups}
        self.version_groups = [
            vg
            for vg in tables.version_groups
            if vg.generation_id <= scope.MAX_GENERATION
            and vg.identifier not in scope.EXCLUDED_VERSION_GROUPS
        ]
        self.types = [
            t
            for t in tables.types
            if t.id < FIRST_SPECIAL_TYPE_ID and t.generation_id <= scope.MAX_GENERATION
        ]
        self.type_slugs = {t.id: t.identifier for t in tables.types}
        self.species = {s.id: s for s in tables.species if s.generation_id <= scope.MAX_GENERATION}
        self.all_species_slugs = {s.id: s.identifier for s in tables.species}
        self.species_names = {
            n.pokemon_species_id: n.name
            for n in tables.species_names
            if n.local_language_id == SPANISH_LANGUAGE_ID
        }
        # Only default forms are loaded (CA-11): one per species.
        self.default_pokemon = {
            p.species_id: p for p in tables.pokemon if p.is_default and p.species_id in self.species
        }
        self.default_form_ids = {f.id for f in tables.pokemon_forms if f.is_default}

    def rows(self) -> Iterator[ReferenceModel]:
        self._check_incense_babies()
        yield from self._generations()
        yield from self._version_groups_and_games()
        yield from self._types()
        yield from self._type_efficacy()
        yield from self._species()
        yield from self._pokemon_types()
        yield from self._evolution_steps()
        yield from self._game_pokemon()

    # --- Games -----------------------------------------------------------------------------

    def _generations(self) -> Iterator[Generation]:
        for generation in self.generations:
            yield Generation(number=generation.id, slug=generation.identifier)

    def _version_groups_and_games(self) -> Iterator[ReferenceModel]:
        names = {
            n.version_id: n.name
            for n in self.t.version_names
            if n.local_language_id == SPANISH_LANGUAGE_ID
        }
        groups = {vg.id: vg for vg in self.version_groups}
        for group in self.version_groups:
            yield VersionGroup(
                slug=group.identifier, generation=group.generation_id, order=group.order
            )
        for version in self.t.versions:
            version_group = groups.get(version.version_group_id)
            if version_group is None:
                continue
            generation = version_group.generation_id
            yield Game(
                slug=version.identifier,
                name_es=_lookup(names, version.id, "Nombre en español del juego"),
                version_group=version_group.identifier,
                generation=generation,
                release_order=version.id,
                has_breeding=generation >= scope.FIRST_BREEDING_GENERATION,
                is_target=generation in scope.TARGET_GENERATIONS,
            )

    # --- Types -----------------------------------------------------------------------------

    def _types(self) -> Iterator[Type]:
        names = {
            n.type_id: n.name
            for n in self.t.type_names
            if n.local_language_id == SPANISH_LANGUAGE_ID
        }
        for type_ in self.types:
            yield Type(
                slug=type_.identifier,
                name_es=_lookup(names, type_.id, "Nombre en español del tipo"),
                generation=type_.generation_id,
            )

    def _type_efficacy(self) -> Iterator[TypeEfficacy]:
        """Type chart of each generation, resolved with the past factors.

        A past factor applies up to and including its ``generation_id``; for generation
        ``g`` the one with the smallest ``generation_id`` >= ``g`` wins.
        """
        current = {
            (e.damage_type_id, e.target_type_id): e.damage_factor for e in self.t.type_efficacy
        }
        past: dict[tuple[int, int], list[TypeEfficacyPastRow]] = defaultdict(list)
        for row in self.t.type_efficacy_past:
            past[(row.damage_type_id, row.target_type_id)].append(row)

        for generation in self.generations:
            existing = [t for t in self.types if t.generation_id <= generation.id]
            for attacking in existing:
                for defending in existing:
                    pair = (attacking.id, defending.id)
                    applicable = [p for p in past[pair] if p.generation_id >= generation.id]
                    if applicable:
                        factor = min(applicable, key=lambda p: p.generation_id).damage_factor
                    else:
                        factor = _lookup(current, pair, "Eficacia de la pareja de tipos")
                    yield TypeEfficacy(
                        generation=generation.id,
                        attacking=attacking.identifier,
                        defending=defending.identifier,
                        factor=factor,
                    )

    # --- Species and forms -----------------------------------------------------------------

    def _species(self) -> Iterator[ReferenceModel]:
        egg_groups = {g.id: g.identifier for g in self.t.egg_groups}
        for species in self.species.values():
            # A pre-evolution of a later generation is left out (Happiny for Chansey): in the
            # loaded generations the species is the first stage of its line.
            origin = self.species.get(species.evolves_from_species_id or 0)
            evolves_from = origin.identifier if origin is not None else None
            name = _lookup(self.species_names, species.id, "Nombre en español de la especie")
            yield Species(
                slug=species.identifier,
                dex_number=species.id,
                name_es=name,
                generation=species.generation_id,
                evolves_from=evolves_from,
                evolution_chain=species.evolution_chain_id,
                is_baby=species.is_baby,
                requires_incense=species.identifier in self.incense_babies,
                is_legendary=species.is_legendary,
                is_mythical=species.is_mythical,
            )
            pokemon = _lookup(self.default_pokemon, species.id, "Forma por defecto de la especie")
            yield Pokemon(
                slug=pokemon.identifier,
                species=species.identifier,
                name_es=name,
                is_default=True,
                pokeapi_id=pokemon.id,
            )
        for row in self.t.species_egg_groups:
            if row.species_id in self.species:
                yield SpeciesEggGroup(
                    species=self.species[row.species_id].identifier,
                    egg_group=_lookup(egg_groups, row.egg_group_id, "Grupo huevo"),
                )

    def _check_incense_babies(self) -> None:
        babies = {s.identifier for s in self.species.values() if s.is_baby}
        unknown = sorted(self.incense_babies - babies)
        if unknown:
            raise TransformError(f"breeding.yaml: {unknown} no son bebés cargados")

    def _pokemon_types(self) -> Iterator[PokemonType]:
        """Types of each form in each generation where it exists, resolved with past types.

        Past types apply up to and including their ``generation_id``; for generation ``g``
        the entry with the smallest ``generation_id`` >= ``g`` wins.
        """
        current: dict[int, list[PokemonTypeRow]] = defaultdict(list)
        for row in self.t.pokemon_types:
            current[row.pokemon_id].append(row)
        past: dict[int, list[PokemonTypePastRow]] = defaultdict(list)
        for past_row in self.t.pokemon_types_past:
            past[past_row.pokemon_id].append(past_row)

        for species_id, pokemon in self.default_pokemon.items():
            species = self.species[species_id]
            for generation in self.generations:
                if species.generation_id > generation.id:
                    continue
                applicable = [p for p in past[pokemon.id] if p.generation_id >= generation.id]
                if applicable:
                    until = min(p.generation_id for p in applicable)
                    types: list[PokemonTypeRow] = [
                        p for p in applicable if p.generation_id == until
                    ]
                else:
                    types = current[pokemon.id]
                if not types:
                    raise TransformError(f"{pokemon.identifier} no tiene tipos")
                for row in types:
                    type_ = self._existing_type(row.type_id, generation.id, pokemon.identifier)
                    yield PokemonType(
                        pokemon=pokemon.identifier,
                        generation=generation.id,
                        slot=row.slot,
                        type=type_,
                    )

    def _existing_type(self, type_id: int, generation: int, pokemon: str) -> str:
        for type_ in self.types:
            if type_.id == type_id:
                if type_.generation_id > generation:
                    break
                return type_.identifier
        raise TransformError(
            f"{pokemon} tendría en la generación {generation} el tipo {type_id}, "
            "que no existe en ella"
        )

    # --- Evolutions ------------------------------------------------------------------------

    def _evolution_steps(self) -> Iterator[EvolutionStep]:
        """Steps that apply in each version group.

        ``version_group_id`` is the group where the evolution was introduced. A row applies
        to a group if it was introduced in that group or an earlier one (by ``order``) and
        both species exist in the group's generation. Rows about non-default forms
        (regional evolutions) are skipped.
        """
        triggers = {t.id: t.identifier for t in self.t.evolution_triggers}
        for group in self.version_groups:
            for row in self.t.evolutions:
                evolved = self.species.get(row.evolved_species_id)
                if evolved is None or evolved.generation_id > group.generation_id:
                    continue
                if evolved.evolves_from_species_id is None:
                    raise TransformError(f"{evolved.identifier} evoluciona pero no tiene origen")
                origin = self.species.get(evolved.evolves_from_species_id)
                if origin is None or origin.generation_id > group.generation_id:
                    continue
                introduced = _lookup(
                    self.all_version_groups, row.version_group_id, "Grupo de versiones"
                )
                if introduced.order > group.order or not self._about_default_forms(row):
                    continue
                yield EvolutionStep(
                    version_group=group.identifier,
                    from_pokemon=self.default_pokemon[origin.id].identifier,
                    to_pokemon=self.default_pokemon[evolved.id].identifier,
                    trigger=_lookup(triggers, row.evolution_trigger_id, "Disparador"),
                    conditions=self._conditions(row),
                )

    def _about_default_forms(self, row: EvolutionRow) -> bool:
        forms = (row.required_pokemon_form_id, row.evolved_pokemon_form_id)
        return all(form is None or form in self.default_form_ids for form in forms)

    def _conditions(self, row: EvolutionRow) -> dict[str, ConditionValue]:
        """Non-empty conditions, with ids replaced by PokeAPI identifiers."""
        references: dict[str, tuple[str, Mapping[int, str]]] = {
            "trigger_item_id": ("trigger_item", {i.id: i.identifier for i in self.t.items}),
            "held_item_id": ("held_item", {i.id: i.identifier for i in self.t.items}),
            "location_id": ("location", {i.id: i.identifier for i in self.t.locations}),
            "known_move_id": ("known_move", {m.id: m.identifier for m in self.t.moves}),
            "used_move_id": ("used_move", {m.id: m.identifier for m in self.t.moves}),
            "known_move_type_id": ("known_move_type", self.type_slugs),
            "party_type_id": ("party_type", self.type_slugs),
            "party_species_id": ("party_species", self.all_species_slugs),
            "trade_species_id": ("trade_species", self.all_species_slugs),
            "region_id": ("region", {r.id: r.identifier for r in self.t.regions}),
        }
        conditions: dict[str, ConditionValue] = {}
        values = row.model_dump(exclude=set(EVOLUTION_ROW_KEYS | FORM_COLUMNS), exclude_none=True)
        for column, value in values.items():
            if column in FLAG_CONDITIONS and value is False:
                continue
            if column in references:
                key, names = references[column]
                conditions[key] = _lookup(names, value, column)
            else:
                conditions[column] = value
        return conditions

    # --- Availability ----------------------------------------------------------------------

    def _game_pokemon(self) -> Iterator[GamePokemon]:
        """Existence and arrival of every loaded form in each target game (RN-03).

        Existence: up to the 7th generation, every species of the National Pokédex up to the
        game's generation can be had in the game, at least by trade, so it is automatic.
        Arrival before completing the game (CA-28): proposed from the game's arrival rule in
        ``arrival.yaml``, or pending if it has none.
        """
        groups = {vg.id: vg for vg in self.version_groups}
        target_games = set()
        for version in self.t.versions:
            group = groups.get(version.version_group_id)
            if group is None or group.generation_id not in scope.TARGET_GENERATIONS:
                continue
            target_games.add(version.identifier)
            rule = self.curated.arrival_rule(version.identifier)
            members = self._pokedex_members(rule.regional_pokedex) if rule else None
            for species_id, pokemon in self.default_pokemon.items():
                species = self.species[species_id]
                if species.generation_id > group.generation_id:
                    continue
                can_arrive, origin = None, Origin.PENDING
                if members is not None:
                    stages = self._stages_from_egg(species)
                    can_arrive = all(stage.id in members for stage in stages)
                    origin = Origin.INFERRED
                yield GamePokemon(
                    game=version.identifier,
                    pokemon=pokemon.identifier,
                    exists_in_game=True,
                    exists_origin=Origin.AUTOMATIC,
                    can_arrive=can_arrive,
                    arrival_origin=origin,
                )
        unknown = sorted(set(self.curated.arrival.games) - target_games)
        if unknown:
            raise TransformError(f"arrival.yaml: {unknown} no son juegos objetivo cargados")

    def _pokedex_members(self, pokedex: str | None) -> set[int] | None:
        """Species ids of a regional Pokédex, or ``None`` if there is no Pokédex."""
        if pokedex is None:
            return None
        ids = {p.identifier: p.id for p in self.t.pokedexes}
        pokedex_id = _lookup(ids, pokedex, "Pokédex")
        return {row.species_id for row in self.t.dex_numbers if row.pokedex_id == pokedex_id}

    def _stages_from_egg(self, species: SpeciesRow) -> list[SpeciesRow]:
        """Stages from the one that hatches from the egg up to ``species`` (CA-25, CA-36).

        The first stage of the line hatches from the egg, unless it is an incense baby: then
        the next stage does (Marill rather than Azurill), except for the baby itself.
        """
        stages = [species]
        while (origin := self.species.get(stages[0].evolves_from_species_id or 0)) is not None:
            stages.insert(0, origin)
        if len(stages) > 1 and stages[0].identifier in self.incense_babies:
            stages = stages[1:]
        return stages
