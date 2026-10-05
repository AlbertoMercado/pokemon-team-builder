/**
 * Keys of the queries, one per resource. A change invalidates the keys of what it affects
 * (adding a favourite invalidates the catalogue, the favourites and the review).
 */
import type { CatalogFilters } from "./pokemon";

export const queryKeys = {
  meta: ["meta"] as const,
  favorites: ["favorites"] as const,
  /** Prefix of every list of the Hall of Fame, whole or filtered by game. */
  hallOfFame: ["hall-of-fame"] as const,
  hallOfFameList: (game: string | undefined) => ["hall-of-fame", game ?? null] as const,
  /** Prefix of every catalogue query: the lists and the details. */
  pokemon: ["pokemon"] as const,
  catalog: (filters: CatalogFilters) => ["pokemon", "list", filters] as const,
  pokemonDetail: (pokemon: string) => ["pokemon", "detail", pokemon] as const,
  games: (all: boolean) => ["games", all] as const,
  /** Prefix of the reviews of every game: they depend on the favourites and the rules. */
  reviews: ["review"] as const,
  review: (game: string) => ["review", game] as const,
  rules: ["rules"] as const,
  /** Prefix of the generations of every game: they depend on favourites, rules and data. */
  generations: ["generation"] as const,
  generation: (game: string) => ["generation", game] as const,
};
