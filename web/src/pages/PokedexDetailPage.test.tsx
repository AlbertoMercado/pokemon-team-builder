import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "../test/render";
import { startPokedex } from "../test/pokedex";

describe("Pokédex: el detalle de registrados e imposibles (RF-24)", () => {
  it("lists them and unmarks a mistake", async () => {
    startPokedex("leafgreen", "bulbasaur", "pikachu");
    renderApp("/pokedex/leafgreen");
    await userEvent.click(
      await screen.findByRole("link", { name: "Ver los registrados y los imposibles" }),
    );

    const registered = within(await screen.findByRole("list", { name: "Registrados" }));
    expect(registered.getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      expect.stringContaining("Bulbasaur"),
      expect.stringContaining("Pikachu"),
    ]);
    await userEvent.click(registered.getByRole("button", { name: "Desmarcar Pikachu" }));
    expect(await screen.findByRole("heading", { name: "Registrados (1)" })).toBeVisible();
  });

  it("does not unmark those only from spin-offs (RN-25)", async () => {
    startPokedex("leafgreen");
    renderApp("/pokedex/leafgreen/detalle");

    const impossible = within(await screen.findByRole("list", { name: "Imposibles" }));
    expect(impossible.getByRole("link", { name: "Jirachi" })).toHaveAttribute(
      "href",
      "/pokedex/leafgreen/pokemon/jirachi",
    );
    expect(impossible.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByText(/solo se obtienen en spin-offs/)).toBeVisible();
  });
});

describe("Pokédex: la ficha de un Pokémon (RF-22, CA-76)", () => {
  it("shows how to obtain it, without skipping", async () => {
    startPokedex("leafgreen");
    renderApp("/pokedex/leafgreen/pokemon/sandshrew");

    const card = within(await screen.findByRole("article", { name: "Ficha de Sandshrew" }));
    expect(
      card.getByText("Transferirlo desde Verde Hoja: Aparece salvaje en Ruta 4: 25 %"),
    ).toBeVisible();
    expect(card.queryByRole("button", { name: "Saltar de momento" })).not.toBeInTheDocument();
  });

  it("says why one cannot be obtained", async () => {
    startPokedex("leafgreen");
    renderApp("/pokedex/leafgreen/pokemon/jirachi");

    expect(await screen.findByText(/Solo se obtiene en spin-offs/)).toBeVisible();
  });
});
