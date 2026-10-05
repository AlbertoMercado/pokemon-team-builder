/** The catalogue (RF-01, RF-02): GET /api/pokemon and GET /api/pokemon/{pokemon}. */
import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import { queryKeys } from "./keys";

/** Filters of the list; `undefined` means no filter. */
export interface CatalogFilters {
  q?: string;
  type?: string;
  favorite?: boolean;
}

export function useCatalog(filters: CatalogFilters) {
  return useQuery({
    queryKey: queryKeys.catalog(filters),
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/api/pokemon", { params: { query: filters }, signal })),
    // Keep the list on screen while the next search is loading.
    placeholderData: keepPreviousData,
  });
}

/** The forms whose name contains `q`, for the Pokémon picker; nothing while `q` is empty. */
export function usePokemonSearch(q: string) {
  const query = q.trim();
  return useQuery({
    queryKey: queryKeys.catalog({ q: query }),
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/api/pokemon", { params: { query: { q: query } }, signal })),
    enabled: query !== "",
    placeholderData: keepPreviousData,
  });
}

/** Name of every loaded form by identifier, from the whole catalogue (it is small). */
export function usePokemonNames() {
  return useQuery({
    queryKey: queryKeys.catalog({}),
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/api/pokemon", { params: { query: {} }, signal })),
    select: (catalog) => new Map(catalog.pokemon.map((entry) => [entry.pokemon, entry.name])),
  });
}

export function usePokemon(pokemon: string) {
  return useQuery({
    queryKey: queryKeys.pokemonDetail(pokemon),
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/api/pokemon/{pokemon}", { params: { path: { pokemon } }, signal })),
  });
}
