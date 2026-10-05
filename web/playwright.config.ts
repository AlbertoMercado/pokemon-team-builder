import { defineConfig, devices } from "@playwright/test";

const PORT = 8765;

// End-to-end tests against the real API, which serves the compiled web (npm run build) over
// the FireRed scenario of the tests, without network (tests/e2e/serve.py). Each run starts it
// with a new temporary data directory.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://127.0.0.1:${String(PORT)}`,
    trace: "on-first-retry",
    locale: "es-ES",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `uv run --directory .. python -m tests.e2e.serve --port ${String(PORT)}`,
    url: `http://127.0.0.1:${String(PORT)}/api/games`,
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
