import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";

import { LOAD_COMMAND, START_COMMAND } from "../lib/commands";
import { renderApp } from "../test/render";
import { server, withoutApi, withoutData } from "../test/server";

describe("Inicio", () => {
  it("shows the favourites, the last completed game and the loaded data", async () => {
    renderApp("/");

    const favorites = await screen.findByRole("link", { name: "2 favoritos" });
    expect(favorites).toHaveAttribute("href", "/favoritos");

    expect(screen.getByRole("link", { name: "Rojo Fuego" })).toHaveAttribute(
      "href",
      "/hall-of-fame",
    );
    expect(screen.getByText(/20 de septiembre de 2026/)).toBeInTheDocument();
    const team = screen.getByRole("list", { name: "Equipo" });
    expect(
      within(team)
        .getAllByRole("listitem")
        .map((item) => item.textContent),
    ).toEqual(["Venusaur", "Lapras"]);

    expect(await screen.findByText("bc92d3b")).toBeInTheDocument();
    expect(screen.getByTitle("firered, leafgreen")).toHaveTextContent("2");
    expect(screen.getByRole("link", { name: "Empezar un juego nuevo" })).toHaveAttribute(
      "href",
      "/juego",
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("invites to add favourites and has no last game when everything is empty", async () => {
    server.use(
      http.get("/api/favorites", () => HttpResponse.json({ total: 0, favorites: [] })),
      http.get("/api/hall-of-fame", () => HttpResponse.json([])),
    );
    renderApp("/");

    expect(await screen.findByText(/Todavía no tienes favoritos/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "catálogo" })).toHaveAttribute("href", "/pokemon");
    expect(
      await screen.findByText("Todavía no has registrado ningún juego completado."),
    ).toBeInTheDocument();
  });

  it("explains how to load the data when there is none (503)", async () => {
    withoutData();
    renderApp("/");

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Hay que cargar los datos");
    expect(alert).toHaveTextContent(LOAD_COMMAND);
    expect(screen.queryByText("Favoritos", { selector: "h2" })).not.toBeInTheDocument();
  });

  it("explains how to start the API when it does not answer", async () => {
    withoutApi();
    renderApp("/");

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("La API no responde");
    expect(alert).toHaveTextContent(START_COMMAND);
  });

  it("shows the message of the API next to the part that failed", async () => {
    server.use(
      http.get("/api/hall-of-fame", () =>
        HttpResponse.json({ detail: "Algo salió mal" }, { status: 500 }),
      ),
    );
    renderApp("/");

    expect(await screen.findByRole("alert")).toHaveTextContent("Algo salió mal");
    expect(await screen.findByRole("link", { name: "2 favoritos" })).toBeInTheDocument();
  });
});
