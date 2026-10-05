/** Renders the application, or a part of it, as it runs: with its `QueryClient` and routes. */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router";

import App from "../App";

export function renderApp(path = "/", ui: ReactElement = <App />) {
  // No retries and no cache between tests: each one sees only its own answers.
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}
