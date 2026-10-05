import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "../test/render";

describe("Ficha", () => {
  it("shows number, name, types and the line by stage with each method (RF-02)", async () => {
    renderApp("/pokemon/haunter");

    expect(await screen.findByRole("heading", { level: 1, name: "Haunter" })).toBeInTheDocument();
    // In the heading and in the line.
    expect(screen.getAllByText("#093")).toHaveLength(2);
    expect(screen.getByText("Aparece en la 1.ª generación.")).toBeInTheDocument();

    const line = screen.getByRole("heading", { name: "Línea evolutiva" }).closest("section");
    const stages = within(line as HTMLElement).getAllByRole("heading", { level: 3 });
    expect(stages.map((stage) => stage.textContent)).toEqual(["Etapa 1", "Etapa 2", "Etapa 3"]);
    expect(screen.getByText(/Desde Gastly:/)).toHaveTextContent("Desde Gastly: Nivel 25");
    expect(screen.getByText(/Desde Haunter:/)).toHaveTextContent("Desde Haunter: Intercambio");
    expect(screen.getByRole("link", { name: "Haunter", current: "page" })).toBeInTheDocument();
  });

  it("navigates to the other forms of the line", async () => {
    renderApp("/pokemon/haunter");
    await userEvent.click(await screen.findByRole("link", { name: "Gengar" }));
    expect(await screen.findByRole("heading", { level: 1, name: "Gengar" })).toBeInTheDocument();
  });

  it("keeps the identifier of an item it does not know", async () => {
    renderApp("/pokemon/ninetales-alola");
    expect(await screen.findByText(/Desde Vulpix de Alola:/)).toHaveTextContent(
      "Desde Vulpix de Alola: ice-stone",
    );
  });

  it("adds and removes the favourite with the star (RF-03)", async () => {
    renderApp("/pokemon/gengar");
    await userEvent.click(await screen.findByRole("button", { name: "Añadir Gengar a favoritos" }));
    const star = await screen.findByRole("button", { name: "Quitar Gengar de favoritos" });
    expect(star).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("★ Favorito")).toBeInTheDocument();
  });

  it("explains that a form does not exist (404)", async () => {
    renderApp("/pokemon/missingno");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "El Pokémon missingno no existe en los datos cargados",
    );
    expect(screen.getByRole("link", { name: "Volver al catálogo" })).toBeInTheDocument();
  });
});
