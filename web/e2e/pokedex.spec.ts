/**
 * The Pokédex of a completed game from end to end, against the real API over the FireRed
 * scenario (tests/e2e/serve.py), which has the Pokédex of FireRed and LeafGreen: record the
 * game → confirm the initial list → register the objective, skip one → correct the detail →
 * removing the Hall of Fame entry warns that its Pokédex goes with it (CA-68).
 *
 * It records LeafGreen and removes it at the end, so it does not change the journey of the
 * new game flow (new-game.spec.ts). The scenario names the games and places by their
 * identifier («Leafgreen», «Pallet Town»).
 */
import { expect, test } from "@playwright/test";

test.afterAll(async ({ request }) => {
  // In case the test failed before removing it.
  const entries = (await (await request.get("/api/hall-of-fame")).json()) as {
    id: number;
    game: string;
  }[];
  for (const entry of entries.filter((found) => found.game === "leafgreen")) {
    await request.delete(`/api/hall-of-fame/${String(entry.id)}`);
  }
});

test("completing the Pokédex of a completed game", async ({ page, request }) => {
  const recorded = await request.post("/api/hall-of-fame", {
    data: { game: "leafgreen", completed_on: "2026-01-10", members: ["charizard"] },
  });
  expect(recorded.ok()).toBe(true);

  // The completed games, with the Pokédex not started.
  await page.goto("/");
  await page
    .getByRole("navigation", { name: "Principal" })
    .getByRole("link", { name: "Pokédex" })
    .click();
  const leafgreen = page
    .getByRole("list", { name: "Juegos superados" })
    .getByRole("listitem")
    .filter({ hasText: "Leafgreen" });
  await expect(leafgreen).toContainText("No iniciada");
  await leafgreen.getByRole("link", { name: "Leafgreen" }).click();

  // The initial list: Bulbasaur is already registered.
  const initial = page.getByRole("region", { name: "Lista inicial" });
  await initial.getByRole("searchbox", { name: "Buscar por nombre" }).fill("bulba");
  await initial.getByRole("checkbox", { name: /Bulbasaur/ }).check();
  await initial.getByRole("button", { name: "Confirmar (1 registrados)" }).click();

  // The objective: Ivysaur, evolving Bulbasaur; registered, Venusaur; skipped, Charmander.
  const objective = page.getByRole("region", { name: "Pokémon objetivo" });
  await expect(objective.getByRole("heading", { name: "Ivysaur" })).toBeVisible();
  await expect(objective.getByText("Evolucionar Bulbasaur: Nivel 16")).toBeVisible();
  await objective.getByRole("button", { name: "Registrado" }).click();
  await expect(objective.getByRole("heading", { name: "Venusaur" })).toBeVisible();
  await objective.getByRole("button", { name: "Saltar de momento" }).click();
  await expect(objective.getByRole("heading", { name: "Charmander" })).toBeVisible();
  await expect(
    objective.getByText("Regalo en Pallet Town si lo elegiste como inicial"),
  ).toBeVisible();
  await expect(page.getByText(/2 de \d+ registrados · En curso/)).toBeVisible();

  // The detail corrects a mistake: Ivysaur was not registered after all.
  await page.getByRole("link", { name: "Ver los registrados y los imposibles" }).click();
  await expect(page.getByRole("heading", { name: "Registrados (2)" })).toBeVisible();
  await page.getByRole("button", { name: "Desmarcar Ivysaur" }).click();
  await expect(page.getByRole("heading", { name: "Registrados (1)" })).toBeVisible();

  // Removing the entry warns that its Pokédex goes with it, and removes it.
  await page
    .getByRole("navigation", { name: "Principal" })
    .getByRole("link", { name: "Hall of Fame" })
    .click();
  const entry = page.getByRole("listitem", { name: /^Leafgreen, / });
  await entry.getByRole("button", { name: "Eliminar" }).click();
  await expect(
    entry.getByText("Se borrará también su Pokédex, con 1 Pokémon registrado."),
  ).toBeVisible();
  await entry.getByRole("button", { name: "Sí, eliminar" }).click();
  await expect(page.getByRole("listitem", { name: /^Leafgreen, / })).toHaveCount(0);
  await page
    .getByRole("navigation", { name: "Principal" })
    .getByRole("link", { name: "Pokédex" })
    .click();
  await expect(page.getByRole("heading", { name: "Pokédex" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Leafgreen" })).toHaveCount(0);
});
