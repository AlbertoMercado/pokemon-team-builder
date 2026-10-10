import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "../test/render";
import { withoutCovers } from "../test/server";

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
      ["Pokédex", "/pokedex"],
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

  it("opens a screen from its address", () => {
    renderApp("/reglas");
    expect(screen.getByRole("heading", { level: 1, name: "Reglas" })).toBeInTheDocument();
  });

  it("says when a page does not exist", () => {
    renderApp("/no-existe");
    expect(
      screen.getByRole("heading", { level: 1, name: "Página no encontrada" }),
    ).toBeInTheDocument();
  });

  it("says who owns the images and where the data come from (CA-56)", () => {
    renderApp("/");
    const footer = within(screen.getByRole("contentinfo"));
    expect(footer.getByText(/Las imágenes de los Pokémon son © Nintendo/)).toBeVisible();
    expect(footer.getByRole("link", { name: "WikiDex" })).toHaveAttribute(
      "href",
      "https://www.wikidex.net/",
    );
  });
});

describe("Aviso de las portadas (RF-18, ADR-0011)", () => {
  it("says who owns the covers and links to the page of each one in WikiDex", async () => {
    renderApp("/");
    const footer = within(screen.getByRole("contentinfo"));

    expect(await footer.findByText(/Las portadas de los juegos son © Nintendo/)).toHaveTextContent(
      "solo en privado",
    );
    expect(
      footer
        .getAllByRole("link", { name: /^portada de / })
        .map((link) => [link.textContent, link.getAttribute("href")]),
    ).toEqual([
      [
        "portada de Rojo",
        "https://www.wikidex.net/wiki/Archivo:Car%C3%A1tula_de_Pok%C3%A9mon_Rojo.jpg",
      ],
      [
        "portada de Rojo Fuego",
        "https://www.wikidex.net/wiki/Archivo:Car%C3%A1tula_de_Rojo_Fuego.png",
      ],
      [
        "portada de Verde Hoja",
        "https://www.wikidex.net/wiki/Archivo:Car%C3%A1tula_de_Verde_Hoja.png",
      ],
    ]);
  });

  it("says nothing about covers after a load without them", async () => {
    withoutCovers();
    renderApp("/");
    await screen.findByRole("heading", { level: 1, name: "Inicio" });
    // Wait until the games have answered: the paragraph would appear then.
    await screen.findByRole("link", { name: "Verde Hoja" });

    expect(screen.queryByText(/Las portadas de los juegos/)).not.toBeInTheDocument();
  });
});
