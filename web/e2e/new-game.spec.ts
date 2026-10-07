/**
 * The flow of a new game from end to end, against the real API over the FireRed scenario
 * (tests/e2e/serve.py): favourites → rules → new game → review → result → choose the team and
 * record it → the next generation excludes what was used (RN-16).
 *
 * The scenario names the games by their identifier («Firered»): it is the extract of the tests,
 * not a real load.
 */
import { expect, test } from "@playwright/test";

// The favourites of the FireRed scenario of the engine (tests/core/scenario.py), but Dragonite,
// which is added from the catalogue.
const FAVORITES = [
  "venusaur", "charizard", "blastoise", "butterfree", "pidgeot", "ninetales", "arcanine",
  "alakazam", "machamp", "tentacruel", "golem", "magneton", "dugtrio", "cloyster", "gengar",
  "exeggutor", "rhydon", "kangaskhan", "starmie", "scyther", "gyarados", "lapras", "vaporeon",
  "jolteon", "flareon", "aerodactyl", "snorlax", "zapdos", "mewtwo",
]; // prettier-ignore

test("a new game from the favourites to the Hall of Fame", async ({ page, request }) => {
  for (const pokemon of FAVORITES) {
    expect((await request.put(`/api/favorites/${pokemon}`)).ok()).toBe(true);
  }

  // Favourites: add Dragonite from the catalogue, with the search in the URL.
  await page.goto("/");
  await page
    .getByRole("navigation", { name: "Principal" })
    .getByRole("link", { name: "Catálogo" })
    .click();
  await page.getByRole("searchbox", { name: "Buscar por nombre" }).fill("dragonite");
  await expect(page).toHaveURL(/\/pokemon\?q=dragonite$/);
  await page.getByRole("button", { name: "Añadir Dragonite a favoritos" }).click();
  await expect(page.getByRole("button", { name: "Quitar Dragonite de favoritos" })).toBeVisible();
  await page
    .getByRole("navigation", { name: "Principal" })
    .getByRole("link", { name: "Favoritos" })
    .click();
  await expect(page.getByText("30 favoritos")).toBeVisible();

  // Rules: a weight is saved and kept after reloading.
  await page
    .getByRole("navigation", { name: "Principal" })
    .getByRole("link", { name: "Reglas" })
    .click();
  const rn06 = page.getByRole("listitem", { name: /^RN-06 / });
  await rn06.getByRole("combobox", { name: /Peso/ }).selectOption("2");
  await page.reload();
  await expect(rn06.getByRole("combobox", { name: /Peso/ })).toHaveValue("2");

  // New game: FireRed, its review and the result.
  await page
    .getByRole("navigation", { name: "Principal" })
    .getByRole("link", { name: "Nuevo juego" })
    .click();
  await page.getByRole("link", { name: /Firered/ }).click();
  await expect(page.getByRole("heading", { name: "Revisión de datos: Firered" })).toBeVisible();
  await expect(page.getByText(/Faltan \d+ datos por confirmar/)).toBeVisible();
  await page.getByRole("button", { name: "Aceptar todas las propuestas" }).click();
  await expect(page.getByText("Todos los datos están confirmados.")).toBeVisible();
  await page.getByRole("link", { name: "Generar el equipo" }).click();

  await expect(page).toHaveURL(/\/juego\/firered\/resultado$/);
  await expect(page.getByText("Equipo completo")).toBeVisible();
  const selector = page.getByRole("region", { name: "Elegir el equipo" });
  const chosen = await selector
    .getByText(/^Equipo elegido:/)
    .locator("..")
    .textContent();
  expect(chosen).toContain("Dragonite");

  // Choose the team and record it in the Hall of Fame.
  await selector.getByRole("textbox", { name: "Notas (opcional)" }).fill("Prueba E2E");
  await selector.getByRole("button", { name: "Comprobar y registrar" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Equipo registrado en el Hall of Fame: Firered",
  );

  // RN-16: the result is generated again without the lines just used.
  const used = page.getByRole("region", { name: "Favoritos descartados" });
  await expect(used.getByRole("heading", { name: "Ya usados en tu recorrido" })).toBeVisible();
  // The starter used is excluded too: RN-21 chooses among the others (CA-62).
  await expect(used.getByText(/^Venusaur queda excluido/)).toBeVisible();
  // The line of Dragonite is never excluded: it is still in the team (RN-16, RN-13).
  await expect(used.getByText(/^Dragonite/)).toHaveCount(0);
  await expect(page.getByRole("list", { name: "Posiciones" }).first()).toContainText("Dragonite");

  // The Hall of Fame shows the entry as the last completed game.
  await page.getByRole("status").getByRole("link", { name: "Ver el Hall of Fame" }).click();
  const entry = page.getByRole("listitem", { name: /^Firered, / });
  await expect(entry.getByText("Último juego completado")).toBeVisible();
  await expect(entry.getByText("Prueba E2E")).toBeVisible();
  // Only the members: each one also holds the list of its types.
  await expect(entry.getByRole("list", { name: "Equipo" }).locator(":scope > li")).toHaveCount(6);
});
