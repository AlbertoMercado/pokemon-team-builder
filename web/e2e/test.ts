/**
 * The `test` of every end-to-end test: Playwright's, but the browser only reaches the local API.
 * Any other request (WikiDex, PokeAPI…) is aborted and fails the test that made it, as the
 * Python tests never use the network (tests/conftest.py): a link that leaves the application by
 * mistake is noticed at once.
 */
import { expect, test as base } from "@playwright/test";

export const test = base.extend({
  context: async ({ context, baseURL }, provide) => {
    const local = new URL(baseURL ?? "http://127.0.0.1").origin;
    await context.route(
      (url) => url.origin !== local,
      (route) => route.abort("blockedbyclient"),
    );
    await provide(context);
  },
});

export { expect };
