/**
 * The API simulated with MSW. The answers are typed with the generated contract, so a change of
 * the API that breaks the web also breaks the compilation of the tests.
 */
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import type { FavoritesOut, HallOfFameEntry, Meta } from "../api/types";

export const meta: Meta = {
  app_version: "0.9.0",
  data: {
    pokeapi_commit: "bc92d3b",
    ingested_at: "2026-10-04T10:00:00Z",
    games: ["firered", "leafgreen"],
  },
};

export const favorites: FavoritesOut = {
  total: 2,
  favorites: [
    {
      pokemon: "venusaur",
      name: "Venusaur",
      dex_number: 3,
      types: ["grass", "poison"],
      added_at: "2026-10-01T09:00:00Z",
    },
    {
      pokemon: "ninetales-alola",
      name: "Ninetales de Alola",
      dex_number: 38,
      types: ["ice", "fairy"],
      added_at: "2026-10-01T09:05:00Z",
    },
  ],
};

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

/** Answers of a working API with data loaded. */
export const handlers = [
  http.get("/api/meta", () => HttpResponse.json(meta)),
  http.get("/api/favorites", () => HttpResponse.json(favorites)),
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
