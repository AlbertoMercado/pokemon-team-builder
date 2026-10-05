/**
 * The generation of the teams of a game (RF-08, RF-09, RF-10): POST /api/games/{game}/generations.
 *
 * It is a calculation without state, so it is a query: it runs when the result screen opens,
 * with «Volver a generar», and again when the favourites or the confirmations change.
 */
import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import { queryKeys } from "./keys";

export function useGeneration(game: string) {
  return useQuery({
    queryKey: queryKeys.generation(game),
    queryFn: async ({ signal }) =>
      unwrap(
        await api.POST("/api/games/{game}/generations", { params: { path: { game } }, signal }),
      ),
    // Only when asked or when its data change, not when the window gets the focus.
    refetchOnWindowFocus: false,
  });
}
