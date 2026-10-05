/**
 * The API simulated with MSW. The answers are typed with the generated contract, so a change of
 * the API that breaks the web also breaks the compilation of the tests.
 *
 * The favourites are kept as state, so adding one with the star changes what the catalogue,
 * the detail and the favourites answer next, as in the API. `resetData` restores it.
 */
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import type {
  CatalogPokemon,
  Evolution,
  FavoritesOut,
  HallOfFameEntry,
  Meta,
  PokemonDetail,
} from "../api/types";

export const meta: Meta = {
  app_version: "0.9.0",
  data: {
    pokeapi_commit: "bc92d3b",
    ingested_at: "2026-10-04T10:00:00Z",
    games: ["firered", "leafgreen"],
  },
};

type Form = Omit<CatalogPokemon, "favorite"> & { generation: number; stage: number };

const form = (
  pokemon: string,
  name: string,
  dex_number: number,
  types: string[],
  stage: number,
  region: string | null = null,
): Form => ({ pokemon, name, dex_number, types, region, stage, generation: region ? 7 : 1 });

/** The forms of the catalogue, in order of the National Pokédex. */
export const FORMS: Form[] = [
  form("bulbasaur", "Bulbasaur", 1, ["grass", "poison"], 1),
  form("ivysaur", "Ivysaur", 2, ["grass", "poison"], 2),
  form("venusaur", "Venusaur", 3, ["grass", "poison"], 3),
  form("vulpix", "Vulpix", 37, ["fire"], 1),
  form("vulpix-alola", "Vulpix de Alola", 37, ["ice"], 1, "alola"),
  form("ninetales", "Ninetales", 38, ["fire"], 2),
  form("ninetales-alola", "Ninetales de Alola", 38, ["ice", "fairy"], 2, "alola"),
  form("gastly", "Gastly", 92, ["ghost", "poison"], 1),
  form("haunter", "Haunter", 93, ["ghost", "poison"], 2),
  form("gengar", "Gengar", 94, ["ghost", "poison"], 3),
];

const evolution = (
  from_pokemon: string,
  to_pokemon: string,
  methods: Evolution["methods"],
): Evolution => ({ from_pokemon, to_pokemon, version_group: "firered-leafgreen", methods });

/** The evolutionary lines: their forms and evolutions. */
const LINES: { forms: string[]; evolutions: Evolution[] }[] = [
  {
    forms: ["bulbasaur", "ivysaur", "venusaur"],
    evolutions: [
      evolution("bulbasaur", "ivysaur", [
        { trigger: "level-up", conditions: { minimum_level: 16 } },
      ]),
      evolution("ivysaur", "venusaur", [
        { trigger: "level-up", conditions: { minimum_level: 32 } },
      ]),
    ],
  },
  {
    forms: ["vulpix", "ninetales"],
    evolutions: [
      evolution("vulpix", "ninetales", [
        { trigger: "use-item", conditions: { trigger_item: "fire-stone" } },
      ]),
    ],
  },
  {
    forms: ["vulpix-alola", "ninetales-alola"],
    evolutions: [
      evolution("vulpix-alola", "ninetales-alola", [
        { trigger: "use-item", conditions: { trigger_item: "ice-stone" } },
      ]),
    ],
  },
  {
    forms: ["gastly", "haunter", "gengar"],
    evolutions: [
      evolution("gastly", "haunter", [{ trigger: "level-up", conditions: { minimum_level: 25 } }]),
      evolution("haunter", "gengar", [{ trigger: "trade", conditions: {} }]),
    ],
  },
];

const INITIAL_FAVORITES = ["venusaur", "ninetales-alola"];
const favoriteSet = new Set(INITIAL_FAVORITES);

/** Restores the favourites of the simulated API. */
export function resetData(): void {
  favoriteSet.clear();
  INITIAL_FAVORITES.forEach((pokemon) => favoriteSet.add(pokemon));
}

function catalogEntry(entry: Form): CatalogPokemon {
  const { pokemon, name, dex_number, types, region } = entry;
  return { pokemon, name, dex_number, types, region, favorite: favoriteSet.has(pokemon) };
}

function findForm(pokemon: string): Form | undefined {
  return FORMS.find((candidate) => candidate.pokemon === pokemon);
}

function favoritesOut(): FavoritesOut {
  const favorites = FORMS.filter((entry) => favoriteSet.has(entry.pokemon)).map((entry) => ({
    pokemon: entry.pokemon,
    name: entry.name,
    dex_number: entry.dex_number,
    types: entry.types,
    added_at: "2026-10-01T09:00:00Z",
  }));
  return { total: favorites.length, favorites };
}

function detail(found: Form): PokemonDetail {
  const line = LINES.find((candidate) => candidate.forms.includes(found.pokemon));
  const members = (line?.forms ?? [found.pokemon]).map((pokemon) => {
    const member = findForm(pokemon) ?? found;
    return { ...catalogEntry(member), stage: member.stage };
  });
  return {
    ...catalogEntry(found),
    generation: found.generation,
    species: found.pokemon.split("-")[0] ?? found.pokemon,
    is_legendary: false,
    is_mythical: false,
    line: members,
    evolutions: line?.evolutions ?? [],
  };
}

export const hallOfFame: HallOfFameEntry[] = [
  {
    id: 1,
    game: "firered",
    game_name: "Rojo Fuego",
    generation: 3,
    completed_on: "2026-09-20",
    notes: null,
    order: 1,
    last: true,
    members: [
      { position: 1, pokemon: "venusaur", name: "Venusaur", types: ["grass", "poison"] },
      { position: 2, pokemon: "lapras", name: "Lapras", types: ["water", "ice"] },
    ],
  },
];

const notFound = (pokemon: string) =>
  HttpResponse.json(
    { detail: `El Pokémon ${pokemon} no existe en los datos cargados` },
    { status: 404 },
  );

/** Answers of a working API with data loaded. */
export const handlers = [
  http.get("/api/meta", () => HttpResponse.json(meta)),
  http.get("/api/pokemon", ({ request }) => {
    const params = new URL(request.url).searchParams;
    const q = params.get("q")?.toLowerCase();
    const type = params.get("type");
    const favorite = params.get("favorite");
    const pokemon = FORMS.map(catalogEntry).filter(
      (entry) =>
        (!q || entry.name.toLowerCase().includes(q) || entry.pokemon.includes(q)) &&
        (!type || entry.types.includes(type)) &&
        (favorite === null || String(entry.favorite) === favorite),
    );
    return HttpResponse.json({ total: pokemon.length, pokemon });
  }),
  http.get<{ pokemon: string }>("/api/pokemon/:pokemon", ({ params }) => {
    const found = findForm(params.pokemon);
    return found ? HttpResponse.json(detail(found)) : notFound(params.pokemon);
  }),
  http.get("/api/favorites", () => HttpResponse.json(favoritesOut())),
  http.put<{ pokemon: string }>("/api/favorites/:pokemon", ({ params }) => {
    const found = findForm(params.pokemon);
    if (!found) return notFound(params.pokemon);
    favoriteSet.add(found.pokemon);
    return HttpResponse.json({
      ...favoritesOut().favorites.find((f) => f.pokemon === found.pokemon),
    });
  }),
  http.delete<{ pokemon: string }>("/api/favorites/:pokemon", ({ params }) => {
    if (!favoriteSet.delete(params.pokemon)) {
      return HttpResponse.json({ detail: `${params.pokemon} no es favorito` }, { status: 404 });
    }
    return new HttpResponse(null, { status: 204 });
  }),
  http.get("/api/hall-of-fame", () => HttpResponse.json(hallOfFame)),
];

export const server = setupServer(...handlers);

const NO_REFERENCE_DATA =
  "No hay datos de referencia: ejecuta la carga de datos (uv run python -m ingest) y reinicia la API";

/** Every request answers 503, as the API does before the first data load. */
export function withoutData(): void {
  server.use(
    http.all("/api/*", () => HttpResponse.json({ detail: NO_REFERENCE_DATA }, { status: 503 })),
  );
}

/** Every request fails to connect, as when the API is not running. */
export function withoutApi(): void {
  server.use(http.all("/api/*", () => HttpResponse.error()));
}
