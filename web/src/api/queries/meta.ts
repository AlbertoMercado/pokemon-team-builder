/** Versions of the application and of the loaded data: GET /api/meta. */
import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import { queryKeys } from "./keys";

export function useMeta() {
  return useQuery({
    queryKey: queryKeys.meta,
    queryFn: async ({ signal }) => unwrap(await api.GET("/api/meta", { signal })),
  });
}
