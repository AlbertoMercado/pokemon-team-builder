/**
 * Keys of the queries, one per resource. A change invalidates the keys of what it affects
 * (adding a favourite invalidates the catalogue, the favourites and the review).
 */
export const queryKeys = {
  meta: ["meta"] as const,
  favorites: ["favorites"] as const,
  hallOfFame: ["hall-of-fame"] as const,
};
