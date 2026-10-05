import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { currentLocation, renderApp } from "../test/render";
import { FORMS } from "../test/server";

async function shownNames(): Promise<(string | null)[]> {
  const list = await screen.findByRole("list", { name: "Pokémon" });
  // Only the rows: each one also holds the list of its types.
  return Array.from(list.children).map(
    (row) => within(row as HTMLElement).getAllByRole("link")[0]?.textContent ?? null,
  );
}

describe("Catálogo", () => {
  it("lists every form with its number, name, types and star (RF-01)", async () => {
    renderApp("/pokemon");

    expect(await shownNames()).toHaveLength(FORMS.length);
    expect(screen.getByText(`${String(FORMS.length)} Pokémon`)).toBeInTheDocument();
    const venusaur = screen.getByRole("link", { name: "Venusaur" }).closest("li");
    expect(venusaur).not.toBeNull();
    const row = within(venusaur as HTMLElement);
    expect(row.getByText("#003")).toBeInTheDocument();
    expect(row.getByText("Planta")).toBeInTheDocument();
    expect(row.getByText("Veneno")).toBeInTheDocument();
    expect(row.getByRole("button", { name: "Quitar Venusaur de favoritos" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("link", { name: "Venusaur" })).toHaveAttribute(
      "href",
      "/pokemon/venusaur",
    );
  });

  it("shows regional forms as entries of their own (RN-05)", async () => {
    renderApp("/pokemon?q=vulpix");
    expect(await shownNames()).toEqual(["Vulpix", "Vulpix de Alola"]);
    const alola = screen.getByRole("link", { name: "Vulpix de Alola" }).closest("li");
    expect(within(alola as HTMLElement).getByText("Hielo")).toBeInTheDocument();
  });

  it("searches by name and keeps the search in the URL", async () => {
    renderApp("/pokemon");
    await shownNames();

    await userEvent.type(screen.getByRole("searchbox", { name: "Buscar por nombre" }), "saur");

    await vi.waitFor(async () => {
      expect(await shownNames()).toEqual(["Bulbasaur", "Ivysaur", "Venusaur"]);
    });
    expect(currentLocation()).toBe("/pokemon?q=saur");
  });

  it("filters by type and by favourite, combined, from the URL", async () => {
    renderApp("/pokemon?type=ice&favorite=true");

    expect(await shownNames()).toEqual(["Ninetales de Alola"]);
    expect(screen.getByRole("combobox", { name: "Tipo" })).toHaveValue("ice");
    expect(screen.getByRole("combobox", { name: "Favoritos" })).toHaveValue("true");
  });

  it("changes the filters and removes them all", async () => {
    renderApp("/pokemon");
    await shownNames();

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Tipo" }), "Fantasma");
    await vi.waitFor(async () => {
      expect(await shownNames()).toEqual(["Gastly", "Haunter", "Gengar"]);
    });
    expect(currentLocation()).toBe("/pokemon?type=ghost");

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Favoritos" }), "false");
    expect(currentLocation()).toBe("/pokemon?type=ghost&favorite=false");

    await userEvent.click(screen.getByRole("button", { name: "Quitar los filtros" }));
    expect(currentLocation()).toBe("/pokemon");
    await vi.waitFor(async () => {
      expect(await shownNames()).toHaveLength(FORMS.length);
    });
  });

  it("says when nothing matches", async () => {
    renderApp("/pokemon?q=mewtwo");
    expect(await screen.findByText("Ningún Pokémon coincide con la búsqueda.")).toBeInTheDocument();
    expect(screen.getByText("0 Pokémon")).toBeInTheDocument();
  });
});
