/**
 * Target games (RF-05) and the review of their unverified data before generating (RF-15,
 * RN-18): GET /api/games and /api/games/{game}/review.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import type { ReviewValue } from "../types";
import { queryKeys } from "./keys";

export function useGames() {
  return useQuery({
    queryKey: queryKeys.games,
    queryFn: async ({ signal }) => unwrap(await api.GET("/api/games", { signal })),
  });
}

export function useReview(game: string) {
  return useQuery({
    queryKey: queryKeys.review(game),
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/api/games/{game}/review", { params: { path: { game } }, signal })),
  });
}

/** Confirms one fact with the proposed value or a corrected one. */
export function useConfirmFact(game: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async ({ factKey, value }: { factKey: string; value: ReviewValue }) =>
      unwrap(
        await api.PUT("/api/games/{game}/review/{fact_key}", {
          params: { path: { game, fact_key: factKey } },
          body: { value },
        }),
      ),
    onSettled: () => client.invalidateQueries({ queryKey: queryKeys.review(game) }),
  });
}

/** Confirms at once every inferred proposal still unconfirmed. */
export function useAcceptProposals(game: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async () =>
      unwrap(
        await api.POST("/api/games/{game}/review/accept-proposals", {
          params: { path: { game } },
        }),
      ),
    onSuccess: (review) => {
      client.setQueryData(queryKeys.review(game), review);
    },
  });
}
