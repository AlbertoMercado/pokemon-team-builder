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

export function usePokemon(pokemon: string) {
  return useQuery({
    queryKey: queryKeys.pokemonDetail(pokemon),
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/api/pokemon/{pokemon}", { params: { path: { pokemon } }, signal })),
  });
}
