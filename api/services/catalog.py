"""The Pokémon catalogue: list with filters and the detail of a form (RF-01, RF-02).

Types are the current ones, those of the latest loaded generation; generation uses those of
the target game (RN-10). Regional forms are entries of their own (RN-05). Searching by name
ignores case and accents and also looks at the identifier.
"""

import unicodedata
from collections import defaultdict

from sqlmodel import Session

from api.errors import NotFoundError
from api.repositories import reference as reference_repo
from api.repositories import user as user_repo
from api.repositories.reference import PokemonRow
from api.schemas.catalog import (
    CatalogOut,
    CatalogPokemonOut,
    EvolutionMethodOut,
    EvolutionOut,
    LineMemberOut,
    PokemonDetailOut,
)
from api.services.images import image_url
from db.reference import Species


def _normalized(text: str) -> str:
    """Lower case, without accents, and with spaces for hyphens (``mr-mime`` → ``mr mime``)."""
    decomposed = unicodedata.normalize("NFKD", text.replace("-", " ").casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _matches(row: PokemonRow, query: str) -> bool:
    wanted = _normalized(query)
    return wanted in _normalized(row.name) or wanted in _normalized(row.slug)


def list_pokemon(
    user: Session,
    reference: Session,
    q: str | None = None,
    type_name: str | None = None,
    favorite: bool | None = None,
) -> CatalogOut:
    favorites = {f.pokemon for f in user_repo.favorites(user)}
    found = [
        _out(row, favorites)
        for row in reference_repo.pokemon_rows(reference)
        if (not q or _matches(row, q))
        and (type_name is None or type_name in row.types)
        and (favorite is None or (row.slug in favorites) == favorite)
    ]
    return CatalogOut(total=len(found), pokemon=found)


def pokemon_detail(user: Session, reference: Session, pokemon: str) -> PokemonDetailOut:
    rows = reference_repo.pokemon_rows(reference, [pokemon])
    if not rows:
        raise NotFoundError(f"El Pokémon {pokemon} no existe en los datos cargados")
    row = rows[0]
    favorites = {f.pokemon for f in user_repo.favorites(user)}
    species = {s.slug: s for s in reference_repo.chain_species(reference, row.evolution_chain)}
    forms = reference_repo.chain_forms(reference, row.evolution_chain)
    members = reference_repo.pokemon_rows(reference, forms)
    stages = {member.slug: _stage(species, member.species) for member in members}
    own = species[row.species]
    methods: dict[tuple[str, str, str], list[EvolutionMethodOut]] = defaultdict(list)
    for group, step in reference_repo.latest_evolution_steps(reference, forms):
        methods[(step.from_pokemon, step.to_pokemon, group)].append(
            EvolutionMethodOut(trigger=step.trigger, conditions=step.conditions)
        )
    canonical = {member.slug: index for index, member in enumerate(members)}
    evolutions = [
        EvolutionOut(from_pokemon=a, to_pokemon=b, version_group=group, methods=found)
        for (a, b, group), found in sorted(
            methods.items(), key=lambda item: (canonical[item[0][1]], canonical[item[0][0]])
        )
    ]
    return PokemonDetailOut(
        **_out(row, favorites).model_dump(),
        generation=own.generation,
        species=own.slug,
        is_legendary=own.is_legendary,
        is_mythical=own.is_mythical,
        line=[
            LineMemberOut(**_out(member, favorites).model_dump(), stage=stages[member.slug])
            for member in sorted(members, key=lambda m: (stages[m.slug], m.dex_number, m.slug))
        ],
        evolutions=evolutions,
    )


def _stage(species: dict[str, Species], slug: str) -> int:
    """1 for the first species of the line, 2 for what it evolves into, and so on."""
    stage, current = 1, species[slug]
    while current.evolves_from is not None and current.evolves_from in species:
        stage, current = stage + 1, species[current.evolves_from]
    return stage


def _out(row: PokemonRow, favorites: set[str]) -> CatalogPokemonOut:
    return CatalogPokemonOut(
        pokemon=row.slug,
        name=row.name,
        dex_number=row.dex_number,
        types=list(row.types),
        region=row.region,
        favorite=row.slug in favorites,
        image_url=image_url(row.slug, row.has_image),
    )
