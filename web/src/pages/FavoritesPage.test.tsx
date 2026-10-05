import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { renderApp } from "../test/render";
import { server } from "../test/server";

describe("Favoritos", () => {
  it("lists the favourites with their total and types (RF-04)", async () => {
    renderApp("/favoritos");

    const list = await screen.findByRole("list", { name: "Favoritos" });
    expect(screen.getByText("2 favoritos")).toBeInTheDocument();
    const names = Array.from(list.children).map(
      (row) => within(row as HTMLElement).getAllByRole("link")[0]?.textContent,
    );
    expect(names).toEqual(["Venusaur", "Ninetales de Alola"]);
    expect(screen.getByText(/Cada favorito es la evolución a la que quieres llegar/)).toBeVisible();
  });

  it("removes a favourite", async () => {
    renderApp("/favoritos");
    await userEvent.click(
      await screen.findByRole("button", { name: "Quitar Venusaur de favoritos" }),
    );
    expect(await screen.findByText("1 favorito")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Venusaur" })).not.toBeInTheDocument();
  });

  it("invites to the catalogue when there are none", async () => {
    server.use(http.get("/api/favorites", () => HttpResponse.json({ total: 0, favorites: [] })));
    renderApp("/favoritos");
    expect(await screen.findByText(/Todavía no tienes favoritos/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "catálogo" })).toHaveAttribute("href", "/pokemon");
  });

  it("shows the message of the API when the star fails", async () => {
    server.use(
      http.delete("/api/favorites/:pokemon", () =>
        HttpResponse.json({ detail: "venusaur no es favorito" }, { status: 404 }),
      ),
    );
    renderApp("/favoritos");
    await userEvent.click(
      await screen.findByRole("button", { name: "Quitar Venusaur de favoritos" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("venusaur no es favorito");
  });
});

describe("La estrella actualiza las tres pantallas", () => {
  it("adds from the catalogue and the detail and favourites show it", async () => {
    renderApp("/pokemon?q=gastly");
    await userEvent.click(await screen.findByRole("button", { name: "Añadir Gastly a favoritos" }));
    expect(
      await screen.findByRole("button", { name: "Quitar Gastly de favoritos" }),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: "Gastly" }));
    expect(
      await screen.findByRole("button", { name: "Quitar Gastly de favoritos" }),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: "Favoritos" }));
    expect(await screen.findByText("3 favoritos")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Quitar Gastly de favoritos" }));
    expect(await screen.findByText("2 favoritos")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("link", { name: "Catálogo" }));
    await userEvent.type(screen.getByRole("searchbox", { name: "Buscar por nombre" }), "gastly");
    expect(
      await screen.findByRole("button", { name: "Añadir Gastly a favoritos" }),
    ).toBeInTheDocument();
  });
});
