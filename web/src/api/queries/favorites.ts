/** The favourites (RF-03, RF-04): GET, PUT and DELETE /api/favorites. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import { queryKeys } from "./keys";

export function useFavorites() {
  return useQuery({
    queryKey: queryKeys.favorites,
    queryFn: async ({ signal }) => unwrap(await api.GET("/api/favorites", { signal })),
  });
}

/** Adds (`favorite: true`) or removes a favourite, and refreshes what shows it. */
export function useSetFavorite() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async ({ pokemon, favorite }: { pokemon: string; favorite: boolean }) => {
      const params = { params: { path: { pokemon } } };
      if (favorite) {
        unwrap(await api.PUT("/api/favorites/{pokemon}", params));
      } else {
        unwrap(await api.DELETE("/api/favorites/{pokemon}", params));
      }
    },
    onSettled: () =>
      Promise.all([
        client.invalidateQueries({ queryKey: queryKeys.pokemon }),
        client.invalidateQueries({ queryKey: queryKeys.favorites }),
        // A favourite brings or takes data to review (RN-18).
        client.invalidateQueries({ queryKey: queryKeys.reviews }),
      ]),
  });
}
