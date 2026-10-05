/** The `QueryClient` of the application: the only store of server state (plan de la web). */
import { QueryClient } from "@tanstack/react-query";

import { NetworkError } from "./client";

const NETWORK_RETRIES = 2;

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Only a failed connection is worth retrying; an answer of the API stays the same.
        retry: (failures, error) => error instanceof NetworkError && failures < NETWORK_RETRIES,
      },
    },
  });
}
