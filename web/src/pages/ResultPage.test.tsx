import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { currentLocation, renderApp } from "../test/render";
import { addFavorite, confirmAll, generationCalls } from "../test/server";

const RESULT = "/juego/firered/resultado";

function rows(table: HTMLElement): string[][] {
  return within(table)
    .getAllByRole("row")
    .map((row) =>
      within(row)
        .queryAllByRole("cell")
        .map((cell) => cell.textContent),
    );
}

describe("Resultado", () => {
  beforeEach(() => {
    confirmAll();
  });

  it("shows the image of the alternatives of each position (RF-17)", async () => {
    addFavorite("dragonite");
    renderApp(RESULT);

    expect(await screen.findByText("Equipo completo")).toBeInTheDocument();
    const team = screen.getByRole("region", { name: "Equipo recomendado" });
    const positions = within(team).getByRole("list", { name: "Posiciones" });
    const cloysterOrLapras = within(positions).getByText("Cloyster o Lapras").closest("li");
    // Only Lapras has an image in these data; Cloyster is still named.
    expect(
      Array.from((cloysterOrLapras as HTMLElement).querySelectorAll("img")).map((image) =>
        image.getAttribute("src"),
      ),
    ).toEqual(["/api/pokemon/lapras/image"]);
  });

  it("shows the complete team of Rojo Fuego with the group «Cloyster o Lapras» (RF-08, RF-09)", async () => {
    addFavorite("dragonite");
    renderApp(RESULT);

    expect(await screen.findByText("Equipo completo")).toBeInTheDocument();
    expect(screen.getByText("Puntuación: 19")).toBeInTheDocument();
    const team = screen.getByRole("region", { name: "Equipo recomendado" });
    const positions = within(team).getByRole("list", { name: "Posiciones" });
    expect(
      Array.from(positions.children).map((position) => position.querySelector("p")?.textContent),
    ).toEqual(["Magneton", "Cloyster o Lapras", "Exeggutor", "Rhydon", "Flareon", "Dragonite"]);
    expect(
      within(team).getByText("Son 2 equipos: elige un Pokémon de cada posición."),
    ).toBeVisible();
    expect(screen.getByText(/Hay 2 equipos empatados/)).toBeInTheDocument();

    const table = within(team).getByRole("table", { name: "Puntuación por regla" });
    expect(rows(table).at(-1)).toEqual(["", "", "19", ""]);
    expect(within(table).getByRole("rowheader", { name: /RN-17/ })).toHaveTextContent(
      "Tipos eficaces frente a los combates clave",
    );

    const discards = screen.getByRole("region", { name: "Favoritos descartados" });
    expect(
      await within(discards).findByText("De tus 3 favoritos, 1 no se puede criar."),
    ).toBeVisible();
    expect(within(discards).getByRole("heading", { name: "No se pueden criar" })).toBeVisible();

    const facts = screen.getByRole("region", { name: "Datos que confirmaste" });
    expect(within(facts).getByText("Concursos: No")).toBeVisible();
    expect(await within(facts).findByText("Equipo de Brock: Geodude, Onix")).toBeVisible();
  });

  it("shows the incomplete team with its reason, slots and suggestions (RF-10)", async () => {
    renderApp(RESULT);

    expect(await screen.findByText("Equipo incompleto")).toBeInTheDocument();
    expect(screen.getByText(/Una regla de presencia necesita un Pokémon/)).toBeInTheDocument();

    const reserved = await screen.findByRole("region", {
      name: "Hueco reservado por RN-13: Dragonite o un Pokémon de tipo primario Dragón",
    });
    expect(within(reserved).getAllByText("Sin verificar")).toHaveLength(2);

    const free = screen.getByRole("region", { name: "3 huecos libres" });
    expect(
      within(free).getByText(
        "Cada sugerencia encaja con el equipo, pero no necesariamente con las demás.",
      ),
    ).toBeVisible();
    const visible = within(free).getByRole("list", { name: "Sugerencias" });
    expect(Array.from(visible.children)).toHaveLength(5);
    // Exeggutor is verified; the rest are not.
    expect(within(visible.children[0] as HTMLElement).queryByText("Sin verificar")).toBeNull();
    expect(within(free).getByText("Ver 2 sugerencias más")).toBeInTheDocument();

    const table = screen.getByRole("table", { name: "Puntuación por regla" });
    expect(within(table).getByRole("rowheader", { name: /RN-15/ }).closest("tr")).toHaveTextContent(
      "Gengar",
    );

    const discards = screen.getByRole("region", { name: "Favoritos descartados" });
    expect(within(discards).getByRole("link", { name: "(dato que confirmaste)" })).toHaveAttribute(
      "href",
      "/juego/firered/revision",
    );
    const presence = screen.getByRole("region", { name: "Reglas de presencia" });
    expect(within(presence).getByText(/Se reserva un hueco \(nivel 3\)/)).toBeVisible();
  });

  it("adds a suggestion to the favourites and generates again", async () => {
    renderApp(RESULT);
    const reserved = await screen.findByRole("region", { name: /Hueco reservado por RN-13/ });

    await userEvent.click(
      within(reserved).getByRole("button", { name: "Añadir Dragonite a favoritos" }),
    );

    expect(await screen.findByText("Equipo completo")).toBeInTheDocument();
    expect(generationCalls.count).toBe(2);
  });

  it("generates again with «Volver a generar»", async () => {
    renderApp(RESULT);
    await screen.findByText("Equipo incompleto");

    await userEvent.click(screen.getByRole("button", { name: "Volver a generar" }));

    await vi.waitFor(() => {
      expect(generationCalls.count).toBe(2);
    });
    expect(await screen.findByRole("button", { name: "Volver a generar" })).toBeEnabled();
  });
});

describe("Resultado con datos pendientes", () => {
  it("leads to the review when the API answers 409 (RN-18)", async () => {
    renderApp(RESULT);

    expect(
      await screen.findByRole("heading", { level: 1, name: "Revisión de datos: Rojo Fuego" }),
    ).toBeInTheDocument();
    expect(currentLocation()).toBe("/juego/firered/revision");
  });
});
