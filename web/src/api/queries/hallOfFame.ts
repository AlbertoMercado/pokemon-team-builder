/** The Hall of Fame: the user's journey (RF-12, RF-13, RN-16): /api/hall-of-fame. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import type { HallOfFameEntryIn } from "../types";
import { queryKeys } from "./keys";

export function useHallOfFame() {
  return useQuery({
    queryKey: queryKeys.hallOfFame,
    queryFn: async ({ signal }) => unwrap(await api.GET("/api/hall-of-fame", { signal })),
  });
}

/**
 * Records a completed game with its team. The journey excludes its lines from then on (RN-16),
 * so the generations and the reviews change too.
 */
export function useAddHallOfFameEntry() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (entry: HallOfFameEntryIn) =>
      unwrap(await api.POST("/api/hall-of-fame", { body: entry })),
    onSuccess: () =>
      Promise.all([
        client.invalidateQueries({ queryKey: queryKeys.hallOfFame }),
        client.invalidateQueries({ queryKey: queryKeys.generations }),
        client.invalidateQueries({ queryKey: queryKeys.reviews }),
      ]),
  });
}
