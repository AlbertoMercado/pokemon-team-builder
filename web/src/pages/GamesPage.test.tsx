import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "../test/render";

describe("Nuevo juego", () => {
  it("offers the target games and leads to the review of the chosen one (RF-05)", async () => {
    renderApp("/juego");

    const list = await screen.findByRole("list", { name: "Juegos" });
    const links = within(list).getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/juego/emerald/revision",
      "/juego/firered/revision",
    ]);

    await userEvent.click(screen.getByRole("link", { name: /Rojo Fuego/ }));
    expect(
      await screen.findByRole("heading", { level: 1, name: "Revisión de datos: Rojo Fuego" }),
    ).toBeInTheDocument();
  });
});
