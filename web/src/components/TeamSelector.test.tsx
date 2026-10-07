import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { currentLocation, renderApp } from "../test/render";
import { addFavorite, confirmAll, generationCalls, requests } from "../test/server";

const RESULT = "/juego/firered/resultado";

async function selector(): Promise<HTMLElement> {
  return screen.findByRole("region", { name: "Elegir el equipo" });
}

describe("Selector del equipo (RF-12, CA-53)", () => {
  beforeEach(() => {
    confirmAll();
  });

  it("chooses an alternative of a position, checks the team and records it", async () => {
    addFavorite("dragonite");
    renderApp(RESULT);
    const panel = within(await selector());

    // «Cloyster o Lapras»: Cloyster is chosen until the user picks Lapras.
    const position = panel.getByRole("group", { name: "Posición 2" });
    expect(within(position).getByRole("radio", { name: "Cloyster" })).toBeChecked();
    await userEvent.click(within(position).getByRole("radio", { name: "Lapras" }));
    expect(panel.getByText(/Equipo elegido:/).parentElement).toHaveTextContent(
      "Equipo elegido: Magneton, Lapras, Exeggutor, Rhydon, Flareon, Dragonite",
    );
    await userEvent.type(panel.getByRole("textbox", { name: "Notas (opcional)" }), "Nuzlocke");
    await userEvent.click(panel.getByRole("button", { name: "Comprobar y registrar" }));

    const done = await screen.findByRole("status");
    expect(done).toHaveTextContent("Equipo registrado en el Hall of Fame: Rojo Fuego");
    expect(within(done).getByRole("link", { name: "Ver el Hall of Fame" })).toHaveAttribute(
      "href",
      "/hall-of-fame",
    );
    const members = ["magneton", "lapras", "exeggutor", "rhydon", "flareon", "dragonite"];
    expect(requests.checks).toEqual([members]);
    expect(requests.entries).toEqual([
      {
        game: "firered",
        completed_on: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/) as string,
        notes: "Nuzlocke",
        members,
      },
    ]);
    // Recorded: the game is completed (CA-68). Asking again answers 409, which does not lead
    // to the review, and the teams are no longer shown.
    await vi.waitFor(() => {
      expect(generationCalls.count).toBe(2);
    });
    expect(done).toHaveTextContent("Rojo Fuego queda completado: ya no aparece en Nuevo juego");
    await vi.waitFor(() => {
      expect(screen.queryByRole("region", { name: "Equipo recomendado" })).not.toBeInTheDocument();
    });
    expect(currentLocation()).toBe(RESULT);
    expect(screen.queryByRole("region", { name: "Elegir el equipo" })).not.toBeInTheDocument();
  });

  it("asks for a suggestion for each slot and does not record a team with problems", async () => {
    renderApp(RESULT);
    const panel = within(await selector());
    const record = panel.getByRole("button", { name: "Comprobar y registrar" });

    expect(record).toBeDisabled();
    expect(panel.getByText("Elige una sugerencia para cada hueco.")).toBeVisible();

    await userEvent.selectOptions(
      panel.getByRole("combobox", { name: "Hueco reservado por RN-13" }),
      "dragonite",
    );
    await userEvent.selectOptions(panel.getByRole("combobox", { name: "Hueco libre 1" }), "rhydon");
    await userEvent.selectOptions(panel.getByRole("combobox", { name: "Hueco libre 2" }), "rhydon");
    await userEvent.selectOptions(
      panel.getByRole("combobox", { name: "Hueco libre 3" }),
      "sandslash",
    );
    expect(panel.getByText("No elijas dos veces el mismo Pokémon.")).toBeVisible();
    expect(record).toBeDisabled();

    await userEvent.selectOptions(
      panel.getByRole("combobox", { name: "Hueco libre 2" }),
      "magneton",
    );
    expect(record).toBeEnabled();
    await userEvent.click(record);

    const problems = await panel.findByRole("alert");
    expect(problems).toHaveTextContent("El equipo no cumple tus reglas, así que no se registra");
    expect(problems).toHaveTextContent("RN-12 Rhydon y Sandslash comparten tipo");
    expect(
      panel.getByText(/Con datos sin verificar: Dragonite, Rhydon, Magneton, Sandslash/),
    ).toBeVisible();
    expect(requests.checks).toEqual([
      ["gengar", "lapras", "dragonite", "rhydon", "magneton", "sandslash"],
    ]);
    expect(requests.entries).toEqual([]);

    // Changing the choice clears the result of the check.
    await userEvent.selectOptions(
      panel.getByRole("combobox", { name: "Hueco libre 3" }),
      "kingler",
    );
    expect(panel.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("discards every team without recording anything", async () => {
    renderApp(RESULT);
    const panel = within(await selector());

    await userEvent.click(panel.getByRole("button", { name: "Descartar los equipos" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Has descartado los equipos: no se ha registrado nada.",
    );
    expect(screen.queryByRole("region", { name: "Elegir el equipo" })).not.toBeInTheDocument();
    expect(requests.checks).toEqual([]);
    expect(requests.entries).toEqual([]);
  });
});
