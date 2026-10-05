/**
 * Keys of the queries, one per resource. A change invalidates the keys of what it affects
 * (adding a favourite invalidates the catalogue, the favourites and the review).
 */
import type { CatalogFilters } from "./pokemon";

export const queryKeys = {
  meta: ["meta"] as const,
  favorites: ["favorites"] as const,
  hallOfFame: ["hall-of-fame"] as const,
  /** Prefix of every catalogue query: the lists and the details. */
  pokemon: ["pokemon"] as const,
  catalog: (filters: CatalogFilters) => ["pokemon", "list", filters] as const,
  pokemonDetail: (pokemon: string) => ["pokemon", "detail", pokemon] as const,
  games: ["games"] as const,
  /** Prefix of the reviews of every game: they depend on the favourites and the rules. */
  reviews: ["review"] as const,
  review: (game: string) => ["review", game] as const,
};
