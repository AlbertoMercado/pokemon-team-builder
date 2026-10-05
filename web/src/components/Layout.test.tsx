import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "../test/render";

describe("Navegación", () => {
  it("links every section and marks the current one", async () => {
    renderApp("/");
    const nav = screen.getByRole("navigation", { name: "Principal" });
    const links = within(nav).getAllByRole("link");
    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      ["Catálogo", "/pokemon"],
      ["Favoritos", "/favoritos"],
      ["Reglas", "/reglas"],
      ["Nuevo juego", "/juego"],
      ["Hall of Fame", "/hall-of-fame"],
    ]);

    await userEvent.click(within(nav).getByRole("link", { name: "Reglas" }));
    expect(screen.getByRole("heading", { level: 1, name: "Reglas" })).toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: "Reglas" })).toHaveAttribute(
      "aria-current",
      "page",
    );

    await userEvent.click(screen.getByRole("link", { name: "pokemon-team-builder" }));
    expect(screen.getByRole("heading", { level: 1, name: "Inicio" })).toBeInTheDocument();
  });

  it("keeps the routes of the later screens", () => {
    renderApp("/hall-of-fame");
    expect(screen.getByRole("heading", { level: 1, name: "Hall of Fame" })).toBeInTheDocument();
  });

  it("says when a page does not exist", () => {
    renderApp("/no-existe");
    expect(
      screen.getByRole("heading", { level: 1, name: "Página no encontrada" }),
    ).toBeInTheDocument();
  });
});
