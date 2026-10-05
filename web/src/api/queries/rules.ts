/** The rules of the catalogue with the user's settings (RF-06, RF-07): /api/rules. */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import type { RulePatch } from "../types";
import { queryKeys } from "./keys";

export function useRules() {
  return useQuery({
    queryKey: queryKeys.rules,
    queryFn: async ({ signal }) => unwrap(await api.GET("/api/rules", { signal })),
  });
}

/** Name of every rule by identifier (`RN-13` → its name). */
export function useRuleNames() {
  return useQuery({
    queryKey: queryKeys.rules,
    queryFn: async ({ signal }) => unwrap(await api.GET("/api/rules", { signal })),
    select: (rules) => new Map(rules.map((rule) => [rule.rule_id, rule.name])),
  });
}

/**
 * Turns a rule on or off or changes its weight. The rules decide the teams and which data take
 * part (RN-17 brings the key battles), so the generations and the reviews change too.
 */
export function useUpdateRule() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async ({ ruleId, change }: { ruleId: string; change: RulePatch }) =>
      unwrap(
        await api.PATCH("/api/rules/{rule_id}", {
          params: { path: { rule_id: ruleId } },
          body: change,
        }),
      ),
    onSuccess: () =>
      Promise.all([
        client.invalidateQueries({ queryKey: queryKeys.rules }),
        client.invalidateQueries({ queryKey: queryKeys.generations }),
        client.invalidateQueries({ queryKey: queryKeys.reviews }),
      ]),
  });
}
