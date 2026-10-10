/**
 * The Pokédex of the completed games (RF-20 to RF-24): /api/pokedex.
 *
 * A mark changes the progress, the objective and the cards that depend on it (registering
 * Pikachu makes Pichu breedable), so every change refreshes every Pokédex query. The skipped
 * Pokémon of the objective are part of its key: they are not kept anywhere (CA-77).
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import type { PokedexMark } from "../types";
import { queryKeys } from "./keys";

/** The completed games with the progress of their Pokédex (RF-20). */
export function usePokedexes() {
  return useQuery({
    queryKey: queryKeys.pokedex,
    queryFn: async ({ signal }) => unwrap(await api.GET("/api/pokedex", { signal })),
  });
}

/** Every species of a game's Pokédex with its marks (RF-21, RF-24). */
export function usePokedex(game: string) {
  return useQuery({
    queryKey: queryKeys.pokedexGame(game),
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/api/pokedex/{game}", { params: { path: { game } }, signal })),
  });
}

/** The card of the next species to register, without the skipped ones (RN-23). */
export function useObjective(game: string, skipped: readonly string[], enabled = true) {
  return useQuery({
    queryKey: queryKeys.pokedexObjective(game, skipped),
    enabled,
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET("/api/pokedex/{game}/objective", {
          params: { path: { game }, query: { skipped: [...skipped] } },
          signal,
        }),
      ),
  });
}

/** The card of a species with every way of obtaining it (RF-22, RF-23). */
export function usePokedexPokemon(game: string, species: string) {
  return useQuery({
    queryKey: queryKeys.pokedexPokemon(game, species),
    queryFn: async ({ signal }) =>
      unwrap(
        await api.GET("/api/pokedex/{game}/pokemon/{species}", {
          params: { path: { game, species } },
          signal,
        }),
      ),
  });
}

function usePokedexChange<T>(change: (variables: T) => Promise<unknown>) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: change,
    onSuccess: () => client.invalidateQueries({ queryKey: queryKeys.pokedex }),
  });
}

/** Confirms the initial list with the species already registered (RF-21). */
export function useStartPokedex(game: string) {
  return usePokedexChange(async (registered: string[]) =>
    unwrap(
      await api.PUT("/api/pokedex/{game}/initial", {
        params: { path: { game } },
        body: { registered },
      }),
    ),
  );
}

/** Registers a species, marks it as impossible or chooses its way (RF-22, RF-23). */
export function useMarkPokemon(game: string) {
  return usePokedexChange(async ({ species, mark }: { species: string; mark: PokedexMark }) =>
    unwrap(
      await api.PUT("/api/pokedex/{game}/pokemon/{species}", {
        params: { path: { game, species } },
        body: mark,
      }),
    ),
  );
}

/** Removes the mark and the chosen way of a species, to correct a mistake (RF-24). */
export function useUnmarkPokemon(game: string) {
  return usePokedexChange(async (species: string) => {
    unwrap(
      await api.DELETE("/api/pokedex/{game}/pokemon/{species}", {
        params: { path: { game, species } },
      }),
    );
  });
}
