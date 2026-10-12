/**
 * Constructors of complete API objects for the simulated API, with sensible defaults: each
 * place states only what matters to it, e.g. `aGame({ game: "leafgreen", name: "Verde Hoja" })`.
 * A new field of a response is added here once, not in every object (#77). The answers are typed
 * with the generated contract, so a field the API adds or removes fails the compilation here.
 */
import type { Game, GeneratedPokemon, ReviewFact, ReviewValue } from "../api/types";

/** A target game of the 3rd generation, not completed and without cover. */
export const aGame = (game: Partial<Game> & Pick<Game, "game" | "name">): Game => ({
  generation: 3,
  version_group: "firered-leafgreen",
  target: true,
  completed: false,
  cover_url: null,
  cover_source_url: null,
  ...game,
});

/** A pending value of the review: inferred if it has a proposal, pending otherwise (RN-18). */
export const aFact = (
  fact_key: string,
  kind: ReviewFact["kind"],
  subject: string,
  name: string,
  proposal: ReviewValue | null,
): ReviewFact => ({
  fact_key,
  kind,
  subject,
  name,
  origin: proposal === null ? "pending" : "inferred",
  proposal,
  status: "pending",
  value: null,
  confirmed_at: null,
  outdated: false,
  source_url: null,
});

/** A Pokémon of a generated team or suggestion, without image. */
export const aGeneratedPokemon = (
  pokemon: string,
  name: string,
  dex_number: number,
  types: string[],
): GeneratedPokemon => ({ pokemon, name, dex_number, types, image_url: null });

/** The same Pokémon with its image, as the API gives it when the load obtained it (RF-17). */
export const withImage = <T extends { pokemon: string }>(found: T): T => ({
  ...found,
  image_url: `/api/pokemon/${found.pokemon}/image`,
});
