/** Renders the application, or a part of it, as it runs: with its `QueryClient` and routes. */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router";

import App from "../App";

export function renderApp(path = "/") {
  // No retries and no cache between tests: each one sees only its own answers.
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

/** Shows the current path and query string, for tests that check the URL. */
function LocationProbe() {
  const { pathname, search } = useLocation();
  return <span data-testid="location">{pathname + search}</span>;
}

/** The current path and query string of the application under test. */
export function currentLocation(): string {
  return screen.getByTestId("location").textContent;
}
