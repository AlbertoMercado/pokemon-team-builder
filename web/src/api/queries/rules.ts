/** The rules of the catalogue with the user's settings (RF-06, RF-07): GET /api/rules. */
import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "../client";
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
