import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "../test/render";
import { server, withoutCovers } from "../test/server";
import { http, HttpResponse } from "msw";

/** The cover of each game card, in order; `null` for a game without cover. */
async function covers(): Promise<(string | null)[]> {
  const list = await screen.findByRole("list", { name: "Juegos" });
  return within(list)
    .getAllByRole("link")
    .map((link) => link.querySelector("img")?.getAttribute("src") ?? null);
}

describe("Nuevo juego", () => {
  it("offers the target games and leads to the review of the chosen one (RF-05)", async () => {
    renderApp("/juego");

    const list = await screen.findByRole("list", { name: "Juegos" });
    const links = within(list).getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/juego/emerald/revision",
      "/juego/firered/revision",
    ]);

    await userEvent.click(within(list).getByRole("link", { name: /Rojo Fuego/ }));
    expect(
      await screen.findByRole("heading", { level: 1, name: "Revisión de datos: Rojo Fuego" }),
    ).toBeInTheDocument();
  });
});

describe("Nuevo juego sin juegos objetivo (RF-25)", () => {
  it("leads to the game catalogue to choose them", async () => {
    server.use(http.get("/api/games", () => HttpResponse.json([])));
    renderApp("/juego");

    expect(await screen.findByText(/Todavía no tienes ningún juego objetivo/)).toBeVisible();
    await userEvent.click(within(screen.getByRole("main")).getByRole("link", { name: "Juegos" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Juegos" })).toBeVisible();
  });
});

describe("Portadas al elegir el juego (RF-18)", () => {
  it("shows the cover of each game next to its name, and the name alone without one", async () => {
    renderApp("/juego");

    // Esmeralda has no cover in the simulated data.
    expect(await covers()).toEqual([null, "/api/games/firered/cover"]);
    expect(screen.getByRole("link", { name: /Esmeralda/ })).toBeVisible();
  });

  it("shows only the names after a load without covers", async () => {
    withoutCovers();
    renderApp("/juego");

    expect(await covers()).toEqual([null, null]);
  });
});
