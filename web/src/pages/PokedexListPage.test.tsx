import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { currentLocation, renderApp } from "../test/render";
import { startPokedex } from "../test/pokedex";
import { server } from "../test/server";

describe("Pokédex: los juegos superados (RF-20)", () => {
  it("is in the navigation and lists each completed game with its progress", async () => {
    startPokedex("leafgreen", "bulbasaur", "pikachu");
    renderApp("/");
    await userEvent.click(
      within(screen.getByRole("navigation", { name: "Principal" })).getByRole("link", {
        name: "Pokédex",
      }),
    );

    const games = await screen.findByRole("list", { name: "Juegos superados" });
    const leafgreen = within(games).getByRole("listitem");
    expect(within(leafgreen).getByRole("link", { name: "Verde Hoja" })).toHaveAttribute(
      "href",
      "/pokedex/leafgreen",
    );
    expect(
      within(leafgreen).getByText("· 2 de 6 registrados · En curso · 1 imposible", {
        exact: false,
      }),
    ).toBeVisible();
    expect(within(leafgreen).getByRole("progressbar")).toHaveAttribute("aria-valuenow", "33");
  });

  it("says a Pokédex is not started until its initial list", async () => {
    renderApp("/pokedex");
    expect(await screen.findByText(/0 de 6 registrados · No iniciada/)).toBeVisible();
  });

  it("without completed games, leads to the Hall of Fame", async () => {
    server.use(http.get("/api/pokedex", () => HttpResponse.json([])));
    renderApp("/pokedex");

    await userEvent.click(await screen.findByRole("link", { name: "Hall of Fame" }));
    expect(currentLocation()).toBe("/hall-of-fame");
  });
});
