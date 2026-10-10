/**
 * The Hall of Fame: the user's journey (RF-12, RF-13, RN-16): /api/hall-of-fame.
 *
 * Recording, correcting or removing an entry changes the journey, so the exclusions of RN-16
 * change too: every change refreshes the Hall of Fame, the generations and the reviews. It also
 * changes the Pokédexes: each completed game has one, removed with its entry (CA-68).
 */
import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import type { HallOfFameEntryIn, HallOfFamePatch } from "../types";
import { queryKeys } from "./keys";

/** The entries in the order of the journey; with `game`, only those of that game. */
export function useHallOfFame(game?: string) {
  return useQuery({
    queryKey: queryKeys.hallOfFameList(game),
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/api/hall-of-fame", { params: { query: { game } }, signal })),
  });
}

function journeyChanged(client: QueryClient) {
  return Promise.all([
    client.invalidateQueries({ queryKey: queryKeys.hallOfFame }),
    client.invalidateQueries({ queryKey: queryKeys.generations }),
    client.invalidateQueries({ queryKey: queryKeys.reviews }),
    client.invalidateQueries({ queryKey: queryKeys.pokedex }),
  ]);
}

/** Records a completed game with its team. */
export function useAddHallOfFameEntry() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (entry: HallOfFameEntryIn) =>
      unwrap(await api.POST("/api/hall-of-fame", { body: entry })),
    onSuccess: () => journeyChanged(client),
  });
}

/** Corrects the game, the date, the notes or the team of an entry. */
export function useUpdateHallOfFameEntry() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, change }: { id: number; change: HallOfFamePatch }) =>
      unwrap(
        await api.PATCH("/api/hall-of-fame/{entry_id}", {
          params: { path: { entry_id: id } },
          body: change,
        }),
      ),
    onSuccess: () => journeyChanged(client),
  });
}

/** Removes an entry, its team and the Pokédex of its game. */
export function useRemoveHallOfFameEntry() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      unwrap(
        await api.DELETE("/api/hall-of-fame/{entry_id}", { params: { path: { entry_id: id } } }),
      );
    },
    onSuccess: () => journeyChanged(client),
  });
}
