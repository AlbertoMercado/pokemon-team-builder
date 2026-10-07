/// <reference types="vitest/config" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development the API runs apart (uvicorn on port 8000): Vite forwards /api to it, so the
// web and the API share the origin and need no CORS (docs/05-operacion/web.md).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    // The end-to-end tests (e2e/) run with Playwright, not with Vitest.
    include: ["src/**/*.test.{ts,tsx}"],
    restoreMocks: true,
  },
});
