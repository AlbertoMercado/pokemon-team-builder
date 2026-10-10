/**
 * The Pokédex of the simulated API (`/api/pokedex`), typed with the contract like the rest of
 * `server.ts`. Every completed game of the simulated Hall of Fame has the same small Pokédex,
 * whose ways of obtaining are fixed: the rules are the API's (tests/core/pokedex), not the
 * web's. The marks and whether each Pokédex is started are kept as state, so a mark changes
 * the progress, the objective and the detail, as in the API; `resetPokedex` restores them.
 */
import { http, HttpResponse } from "msw";

import type {
  ObtentionMethod,
  ObtentionWay,
  Pokedex,
  PokedexGame,
  PokedexMark,
  PokedexPokemon,
  PokedexProgress,
} from "../api/types";

type Status = "registered" | "impossible";

const way = (overrides: Partial<ObtentionWay> & Pick<ObtentionWay, "kind">): ObtentionWay => ({
  location: "pallet-town",
  location_name: "Pueblo Paleta",
  area: null,
  method: "gift",
  rarity: 100,
  times: [],
  choice: null,
  item: null,
  conditions: [],
  alternatives: [],
  ...overrides,
});

const method = (
  overrides: Partial<ObtentionMethod> & Pick<ObtentionMethod, "kind" | "key">,
): ObtentionMethod => ({
  recommended: false,
  chosen: false,
  way: null,
  game: null,
  game_name: null,
  pokemon: null,
  pokemon_name: null,
  pokemon_registered: false,
  evolution: null,
  incense: false,
  ...overrides,
});

interface Species {
  species: string;
  name: string;
  types: string[];
  automatically_impossible?: boolean;
  methods: ObtentionMethod[];
}

/** The Pokédex of every completed game: a starter, its evolution, a wild one, a transfer, an
 * event and one only from spin-offs. */
export const POKEDEX_SPECIES: Species[] = [
  {
    species: "bulbasaur",
    name: "Bulbasaur",
    types: ["grass", "poison"],
    methods: [
      method({
        kind: "starter_gift",
        key: "starter_gift:gift@pallet-town+starter-bulbasaur",
        way: way({ kind: "starter_gift", choice: "starter-bulbasaur" }),
      }),
    ],
  },
  {
    species: "ivysaur",
    name: "Ivysaur",
    types: ["grass", "poison"],
    methods: [
      method({
        kind: "evolve",
        key: "evolve:bulbasaur:level-up:minimum_level=16",
        pokemon: "bulbasaur",
        pokemon_name: "Bulbasaur",
        evolution: { trigger: "level-up", conditions: { minimum_level: 16 } },
      }),
    ],
  },
  {
    species: "pikachu",
    name: "Pikachu",
    types: ["electric"],
    methods: [
      method({
        kind: "in_game",
        key: "in_game:walk@viridian-forest",
        way: way({
          kind: "wild",
          location: "viridian-forest",
          location_name: "Bosque Verde",
          method: "walk",
          rarity: 5,
        }),
      }),
      method({
        kind: "transfer",
        key: "transfer:firered",
        game: "firered",
        game_name: "Rojo Fuego",
        way: way({
          kind: "wild",
          location: "viridian-forest",
          location_name: "Bosque Verde",
          method: "walk",
          rarity: 5,
        }),
      }),
    ],
  },
  {
    species: "sandshrew",
    name: "Sandshrew",
    types: ["ground"],
    methods: [
      method({
        kind: "transfer",
        key: "transfer:leafgreen",
        game: "leafgreen",
        game_name: "Verde Hoja",
        way: way({
          kind: "wild",
          location: "kanto-route-4",
          location_name: "Ruta 4",
          method: "walk",
          rarity: 25,
        }),
      }),
    ],
  },
  {
    species: "mew",
    name: "Mew",
    types: ["psychic"],
    methods: [method({ kind: "event", key: "event" })],
  },
  {
    species: "jirachi",
    name: "Jirachi",
    types: ["steel", "psychic"],
    automatically_impossible: true,
    methods: [],
  },
];

interface Marks {
  started: boolean;
  status: Map<string, Status>;
  chosen: Map<string, string>;
}

const pokedexes = new Map<string, Marks>();

function marksOf(game: string): Marks {
  let found = pokedexes.get(game);
  if (found === undefined) {
    found = { started: false, status: new Map(), chosen: new Map() };
    pokedexes.set(game, found);
  }
  return found;
}

/** Restores every Pokédex: none started, nothing marked. */
export function resetPokedex(): void {
  pokedexes.clear();
}

/** Starts the Pokédex of `game` with `registered`, as if done before the test. */
export function startPokedex(game: string, ...registered: string[]): void {
  const marks = marksOf(game);
  marks.started = true;
  registered.forEach((species) => marks.status.set(species, "registered"));
}

function progressOf(marks: Marks): PokedexProgress {
  const total = POKEDEX_SPECIES.length;
  const registered = [...marks.status.values()].filter((s) => s === "registered").length;
  const impossible = POKEDEX_SPECIES.filter(
    (s) =>
      marks.status.get(s.species) === "impossible" ||
      (s.automatically_impossible === true && !marks.status.has(s.species)),
  ).length;
  return {
    registered,
    total,
    impossible,
    percent: Math.floor((registered * 100) / total),
    status: !marks.started ? "not_started" : registered === total ? "completed" : "in_progress",
  };
}

function card(game: string, entry: Species): PokedexPokemon {
  const marks = marksOf(game);
  const chosen = marks.chosen.get(entry.species) ?? null;
  const number = POKEDEX_SPECIES.indexOf(entry) + 1;
  return {
    species: entry.species,
    number,
    name: entry.name,
    pokemon: entry.species,
    types: entry.types,
    image_url: null,
    artwork_url: null,
    status: marks.status.get(entry.species) ?? null,
    automatically_impossible: entry.automatically_impossible ?? false,
    chosen_method: chosen,
    methods: entry.methods.map((m, index) => ({
      ...m,
      recommended: index === 0,
      chosen: m.key === chosen,
      pokemon_registered: m.pokemon !== null && marks.status.get(m.pokemon) === "registered",
    })),
  };
}

function pokedexOut(game: string, name: string, entry: number): Pokedex {
  const marks = marksOf(game);
  return {
    game,
    game_name: name,
    hall_of_fame_entry: entry,
    progress: progressOf(marks),
    species: POKEDEX_SPECIES.map((s) => {
      const found = card(game, s);
      return {
        species: found.species,
        number: found.number,
        name: found.name,
        pokemon: found.pokemon,
        types: found.types,
        image_url: found.image_url,
        status: found.status,
        automatically_impossible: found.automatically_impossible,
      };
    }),
  };
}

const notCompleted = (game: string) =>
  HttpResponse.json(
    { detail: `El juego ${game} no está en el Hall of Fame: no tiene Pokédex` },
    { status: 404 },
  );

const notStarted = () =>
  HttpResponse.json({ detail: "Confirma antes la lista inicial de la Pokédex" }, { status: 409 });

/** A completed game of the simulated Hall of Fame: its name, cover and entry. */
export interface CompletedGame {
  game: string;
  name: string;
  cover_url: string | null;
  entry: number;
}

/** The handlers, over the completed games that `completed` gives, in journey order. */
export function pokedexHandlers(completed: () => CompletedGame[]) {
  const find = (game: string) => completed().find((found) => found.game === game);
  const species = (slug: string) => POKEDEX_SPECIES.find((s) => s.species === slug);
  return [
    http.get("/api/pokedex", () =>
      HttpResponse.json(
        completed().map((found): PokedexGame => ({
          game: found.game,
          game_name: found.name,
          cover_url: found.cover_url,
          hall_of_fame_entry: found.entry,
          progress: progressOf(marksOf(found.game)),
        })),
      ),
    ),
    http.get<{ game: string }>("/api/pokedex/:game", ({ params }) => {
      const found = find(params.game);
      return found
        ? HttpResponse.json(pokedexOut(found.game, found.name, found.entry))
        : notCompleted(params.game);
    }),
    http.put<{ game: string }, { registered: string[] }>(
      "/api/pokedex/:game/initial",
      async ({ params, request }) => {
        const found = find(params.game);
        if (!found) return notCompleted(params.game);
        if (marksOf(found.game).started) {
          return HttpResponse.json(
            { detail: "La lista inicial ya está confirmada" },
            { status: 409 },
          );
        }
        startPokedex(found.game, ...(await request.json()).registered);
        return HttpResponse.json(pokedexOut(found.game, found.name, found.entry));
      },
    ),
    http.get<{ game: string }>("/api/pokedex/:game/objective", ({ params, request }) => {
      const found = find(params.game);
      if (!found) return notCompleted(params.game);
      const skipped = new URL(request.url).searchParams.getAll("skipped");
      const marks = marksOf(found.game);
      const next = POKEDEX_SPECIES.find(
        (s) =>
          !marks.status.has(s.species) &&
          s.automatically_impossible !== true &&
          !skipped.includes(s.species),
      );
      return HttpResponse.json({ pokemon: next ? card(found.game, next) : null });
    }),
    http.get<{ game: string; species: string }>(
      "/api/pokedex/:game/pokemon/:species",
      ({ params }) => {
        const found = find(params.game);
        const entry = species(params.species);
        if (!found) return notCompleted(params.game);
        return entry
          ? HttpResponse.json(card(found.game, entry))
          : HttpResponse.json({ detail: "No está en la Pokédex" }, { status: 404 });
      },
    ),
    http.put<{ game: string; species: string }, PokedexMark>(
      "/api/pokedex/:game/pokemon/:species",
      async ({ params, request }) => {
        const found = find(params.game);
        const entry = species(params.species);
        if (!found || !entry) return notCompleted(params.game);
        const marks = marksOf(found.game);
        if (!marks.started) return notStarted();
        const change = await request.json();
        if ("status" in change) {
          if (change.status) marks.status.set(entry.species, change.status);
          else marks.status.delete(entry.species);
        }
        if ("chosen_method" in change) {
          if (change.chosen_method) marks.chosen.set(entry.species, change.chosen_method);
          else marks.chosen.delete(entry.species);
        }
        return HttpResponse.json(card(found.game, entry));
      },
    ),
    http.delete<{ game: string; species: string }>(
      "/api/pokedex/:game/pokemon/:species",
      ({ params }) => {
        const found = find(params.game);
        if (!found) return notCompleted(params.game);
        const marks = marksOf(found.game);
        if (!marks.started) return notStarted();
        marks.status.delete(params.species);
        marks.chosen.delete(params.species);
        return new HttpResponse(null, { status: 204 });
      },
    ),
  ];
}

/** Removes the Pokédex of `game`, as removing its Hall of Fame entry does (CA-68). */
export function removePokedex(game: string): void {
  pokedexes.delete(game);
}
