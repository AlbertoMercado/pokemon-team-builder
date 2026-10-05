/** The favourites (RF-03, RF-04): GET /api/favorites. */
import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import { queryKeys } from "./keys";

export function useFavorites() {
  return useQuery({
    queryKey: queryKeys.favorites,
    queryFn: async ({ signal }) => unwrap(await api.GET("/api/favorites", { signal })),
  });
}
