/** The Hall of Fame: the user's journey (RF-12, RF-13, RN-16): GET /api/hall-of-fame. */
import { useQuery } from "@tanstack/react-query";

import { api, unwrap } from "../client";
import { queryKeys } from "./keys";

export function useHallOfFame() {
  return useQuery({
    queryKey: queryKeys.hallOfFame,
    queryFn: async ({ signal }) => unwrap(await api.GET("/api/hall-of-fame", { signal })),
  });
}
