/**
 * The layout of the lists, measured in a real browser at 360 px and on the desktop, against the
 * real API over the FireRed scenario (tests/e2e/serve.py). jsdom does not lay out, so the unit
 * tests cannot notice these faults, which reached published versions:
 *
 * - every row of the catalogue and of the favourites is as tall as the others, and the star is
 *   in the same place in all of them (#68);
 * - every image and cover keeps its square box, whatever its shape (#65): the scenario's images
 *   are tall, wide and small on purpose;
 * - every card of the initial list of a Pokédex and of a team in the Hall of Fame is as tall as
 *   the others (#105), also at 768 px, where three columns made two long types wrap.
 *
 * It records LeafGreen in the Hall of Fame and some favourites, and removes them at the end, so
 * it does not change the other flows (new-game.spec.ts, pokedex.spec.ts).
 */
import type { APIRequestContext, Locator, Page } from "@playwright/test";

import { expect, test } from "./test";

const VIEWPORTS = [
  { name: "móvil", width: 360, height: 740 },
  { name: "tableta", width: 768, height: 1024 },
  { name: "escritorio", width: 1280, height: 800 },
];
// Short and long names, one and two types: what made the rows differ (#68).
const FAVORITES = ["mr-mime", "charizard", "snorlax", "nidoqueen", "farfetchd", "kangaskhan"];
// With the longest pairs of types in Spanish («Fantasma, Veneno», «Eléctrico, Volador»), which
// did not fit in the narrow cards of a three-column grid at 768 px.
const TEAM = ["venusaur", "charizard", "gengar", "zapdos", "snorlax", "mr-mime"];
// The borders of `divide-y` make the rows differ by up to one pixel.
const TOLERANCE = 1;

interface Box {
  width: number;
  height: number;
  left: number;
}

async function removeLeafGreen(request: APIRequestContext) {
  const entries = (await (await request.get("/api/hall-of-fame")).json()) as {
    id: number;
    game: string;
  }[];
  for (const entry of entries.filter((found) => found.game === "leafgreen")) {
    await request.delete(`/api/hall-of-fame/${String(entry.id)}`);
  }
}

test.beforeAll(async ({ request }) => {
  // RF-25: Fire Red is a target game, for the covers of «Nuevo juego».
  const chosen = await request.put("/api/game-catalog/firered", {
    data: { selected: true, playable: true },
  });
  expect(chosen.ok()).toBe(true);
  for (const pokemon of FAVORITES) {
    expect((await request.put(`/api/favorites/${pokemon}`)).ok()).toBe(true);
  }
  const recorded = await request.post("/api/hall-of-fame", {
    data: { game: "leafgreen", completed_on: "2026-01-10", members: TEAM },
  });
  expect(recorded.ok()).toBe(true);
});

test.afterAll(async ({ request }) => {
  for (const pokemon of FAVORITES) {
    await request.delete(`/api/favorites/${pokemon}`);
  }
  await removeLeafGreen(request);
});

/** Lazy images only load when they come into view: load them all before measuring. */
async function loadImages(page: Page) {
  await page.locator("img").evaluateAll(async (images) => {
    await Promise.all(
      (images as HTMLImageElement[]).map(async (image) => {
        image.loading = "eager";
        await image.decode().catch(() => undefined);
      }),
    );
  });
}

async function boxes(elements: Locator): Promise<Box[]> {
  return elements.evaluateAll((found) =>
    found.map((element) => {
      const rect = element.getBoundingClientRect();
      return { width: rect.width, height: rect.height, left: rect.left };
    }),
  );
}

/** Every element measures the same, within the tolerance; ``what`` names them on failure. */
async function expectSameHeight(elements: Locator, what: string) {
  const heights = (await boxes(elements)).map((box) => box.height);
  expect(heights.length, `${what}: no hay ninguno`).toBeGreaterThan(1);
  expect(
    Math.max(...heights) - Math.min(...heights),
    `${what}: alturas ${heights.join(", ")}`,
  ).toBeLessThanOrEqual(TOLERANCE);
}

/** Every image is in its square box of ``size`` pixels, whatever the shape of its file. */
async function expectImageBoxes(images: Locator, size: number, what: string) {
  const found = await boxes(images);
  expect(found.length, `${what}: no hay ninguna imagen`).toBeGreaterThan(0);
  const wrong = found.filter(
    (box) => Math.abs(box.width - size) > 0.5 || Math.abs(box.height - size) > 0.5,
  );
  expect(wrong, `${what}: imágenes fuera de su caja de ${String(size)} px`).toEqual([]);
}

/** The rows of a list of Pokémon with the star (RF-01, RF-04, #68). */
async function expectStarredRows(list: Locator, what: string) {
  const rows = list.locator(":scope > li");
  await expectSameHeight(rows, what);
  const stars = await boxes(list.getByRole("button", { name: /favoritos$/ }));
  const lefts = stars.map((star) => star.left);
  expect(stars.length, `${what}: una estrella por fila`).toBe(await rows.count());
  expect(
    Math.max(...lefts) - Math.min(...lefts),
    `${what}: estrellas en ${lefts.join(", ")}`,
  ).toBeLessThanOrEqual(TOLERANCE);
  await expectImageBoxes(list.locator("img"), 40, what);
}

for (const viewport of VIEWPORTS) {
  test.describe(`a ${String(viewport.width)} px (${viewport.name})`, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height } });

    test("the catalogue and the favourites", async ({ page }) => {
      await page.goto("/pokemon");
      const catalogue = page.getByRole("list", { name: "Pokémon" });
      await expect(catalogue.locator(":scope > li")).toHaveCount(145);
      await loadImages(page);
      await expectStarredRows(catalogue, "catálogo");

      await page.goto("/favoritos");
      const favorites = page.getByRole("list", { name: "Favoritos" });
      await expect(favorites.locator(":scope > li")).toHaveCount(FAVORITES.length);
      await loadImages(page);
      await expectStarredRows(favorites, "favoritos");
    });

    test("the detail of a Pokémon", async ({ page }) => {
      await page.goto("/pokemon/venusaur");
      await expect(page.getByRole("heading", { name: "Venusaur" })).toBeVisible();
      await loadImages(page);
      // The artwork and the line, whose rows have the sprite.
      const main = page.getByRole("main");
      await expectImageBoxes(main.locator('img[width="160"]'), 160, "ilustración");
      await expectImageBoxes(main.locator('img[width="40"]'), 40, "línea evolutiva");
    });

    test("the covers of the games", async ({ page }) => {
      await page.goto("/juego");
      const games = page.getByRole("list", { name: "Juegos" });
      await expect(games.locator(":scope > li")).toHaveCount(1); // LeafGreen is completed (CA-68)
      await loadImages(page);
      await expectImageBoxes(games.locator("img"), 96, "nuevo juego");

      await page.goto("/pokedex");
      const pokedexes = page.getByRole("list", { name: "Juegos superados" });
      await expect(pokedexes.locator(":scope > li")).toHaveCount(1);
      await loadImages(page);
      await expectImageBoxes(pokedexes.locator("img"), 64, "Pokédex");
    });

    test("the team of a Hall of Fame entry", async ({ page }) => {
      await page.goto("/hall-of-fame");
      const entry = page.getByRole("listitem", { name: /^Leafgreen, / });
      const team = entry.getByRole("list", { name: "Equipo" }).locator(":scope > li");
      await expect(team).toHaveCount(TEAM.length);
      await loadImages(page);
      await expectSameHeight(team, "equipo del Hall of Fame");
      await expectImageBoxes(team.locator("img"), 40, "equipo del Hall of Fame");
      await expectImageBoxes(entry.locator("img").first(), 40, "portada del registro");
    });

    test("the initial list of a Pokédex", async ({ page }) => {
      await page.goto("/pokedex/leafgreen");
      const cards = page
        .getByRole("list", { name: "Pokémon de la lista inicial" })
        .locator(":scope > li");
      await expect(cards.first()).toBeVisible();
      await loadImages(page);
      await expectSameHeight(cards, "lista inicial de la Pokédex");
      await expectImageBoxes(cards.locator("img"), 40, "lista inicial de la Pokédex");
    });
  });
}
