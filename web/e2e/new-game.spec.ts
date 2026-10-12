/**
 * The flow of a new game from end to end, against the real API over the FireRed scenario
 * (tests/e2e/serve.py): choose the target games in the game catalogue → favourites → rules →
 * new game → review → result → choose the team and record it → the next generation excludes
 * what was used (RN-16).
 *
 * The scenario names the games by their identifier («Firered»): it is the extract of the tests,
 * not a real load.
 */
import { expect, test } from "./test";

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

  // RF-25: Fire Red and Leaf Green are target games only once chosen in the game catalogue;
  // their playability is not known, so the screen asks (CA-92).
  await page.goto("/");
  await page
    .getByRole("navigation", { name: "Principal" })
    .getByRole("link", { name: "Juegos", exact: true })
    .click();
  for (const name of ["Firered", "Leafgreen"]) {
    const card = page.getByRole("listitem", { name });
    // Another spec may have answered already (layout.spec.ts): then it does not ask again.
    await expect(card.getByRole("button", { name: "Elegir como juego objetivo" })).toBeVisible();
    const answered = (await card.getByText(/Has indicado que puedes jugarlo/).count()) > 0;
    await card.getByRole("button", { name: "Elegir como juego objetivo" }).click();
    if (!answered) {
      await card.getByRole("button", { name: "Sí" }).click();
    }
    await expect(card.getByText("Juego objetivo")).toBeVisible();
  }

  // Favourites: add Dragonite from the catalogue, with the search in the URL.
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
  // In the list of games: the notice at the foot also links the cover of each game.
  const games = page.getByRole("list", { name: "Juegos" });
  await games.getByRole("link", { name: /Firered/ }).click();
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

  // CA-68: Fire Red is completed: it is no longer offered in «Nuevo juego».
  await expect(page.getByRole("status")).toContainText("Firered queda completado");
  await expect(page.getByRole("region", { name: "Equipo recomendado" })).toHaveCount(0);

  // The Hall of Fame shows the entry as the last completed game.
  await page.getByRole("status").getByRole("link", { name: "Ver el Hall of Fame" }).click();
  const entry = page.getByRole("listitem", { name: /^Firered, / });
  await expect(entry.getByText("Último juego completado")).toBeVisible();
  await expect(entry.getByText("Prueba E2E")).toBeVisible();
  // Only the members: each one also holds the list of its types.
  await expect(entry.getByRole("list", { name: "Equipo" }).locator(":scope > li")).toHaveCount(6);

  // CA-68: «Nuevo juego» no longer offers Fire Red, only Leaf Green.
  await page.goto("/juego");
  await expect(games.getByRole("link", { name: /Leafgreen/ })).toBeVisible();
  await expect(games.getByRole("link", { name: /Firered/ })).toHaveCount(0);
});
