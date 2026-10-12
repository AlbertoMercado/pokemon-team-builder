/** The game catalogue (RF-25): GET and PUT /api/game-catalog. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import { queryKeys } from "./keys";

export function useGameCatalog() {
  return useQuery({
    queryKey: queryKeys.gameCatalog,
    queryFn: async ({ signal }) => unwrap(await api.GET("/api/game-catalog", { signal })),
  });
}

/** Selects a game or not, and answers whether it is playable on a current system (CA-92). */
export function useChooseGame() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async ({
      game,
      selected,
      playable,
    }: {
      game: string;
      selected?: boolean;
      playable?: boolean;
    }) =>
      unwrap(
        await api.PUT("/api/game-catalog/{game}", {
          params: { path: { game } },
          body: { selected: selected ?? null, playable: playable ?? null },
        }),
      ),
    // The answer about playability is kept even when the selection is refused (409).
    onSettled: () =>
      Promise.all([
        client.invalidateQueries({ queryKey: queryKeys.gameCatalog }),
        client.invalidateQueries({ queryKey: queryKeys.gamesPrefix }),
      ]),
  });
}
