import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { currentLocation, renderApp } from "../test/render";
import { server } from "../test/server";

async function journey(): Promise<string[]> {
  const list = await screen.findByRole("list", { name: "Recorrido" });
  return Array.from(list.children).map((entry) => entry.getAttribute("aria-label") ?? "");
}

async function record(game: string, date: string, ...names: string[]) {
  await userEvent.click(screen.getByRole("button", { name: "Registrar un equipo" }));
  const form = within(screen.getByRole("form", { name: "Registrar un equipo" }));
  await userEvent.selectOptions(form.getByRole("combobox", { name: "Juego" }), game);
  const dateField = form.getByLabelText("Fecha");
  await userEvent.clear(dateField);
  await userEvent.type(dateField, date);
  for (const name of names) {
    await userEvent.type(
      form.getByRole("searchbox", { name: "Añadir un Pokémon al equipo" }),
      name,
    );
    await userEvent.click(await form.findByRole("button", { name: `Añadir ${name}` }));
  }
  return form;
}

describe("Hall of Fame (RF-12, RF-13)", () => {
  it("shows the journey with the team and the last completed game", async () => {
    renderApp("/hall-of-fame");

    expect(await journey()).toEqual(["Rojo Fuego, 20 de septiembre de 2026"]);
    const entry = within(screen.getByRole("listitem", { name: /Rojo Fuego/ }));
    expect(entry.getByText("Último juego completado")).toBeVisible();
    const team = entry.getByRole("list", { name: "Equipo" });
    expect(within(team).getByText("Lapras")).toBeVisible();
    expect(within(team).getByText("Hielo")).toBeVisible();
  });

  it("records by hand a game that is not a target game, in the order of the journey", async () => {
    renderApp("/hall-of-fame");
    await journey();

    const form = await record("Rojo", "2026-01-15", "Gengar");
    await userEvent.type(form.getByRole("textbox", { name: "Notas (opcional)" }), "Primera vez");
    await userEvent.click(form.getByRole("button", { name: "Guardar" }));

    await vi.waitFor(async () => {
      expect(await journey()).toEqual([
        "Rojo, 15 de enero de 2026",
        "Rojo Fuego, 20 de septiembre de 2026",
      ]);
    });
    const red = within(screen.getByRole("listitem", { name: /^Rojo, / }));
    expect(red.getByText("Primera vez")).toBeVisible();
    expect(red.queryByText("Último juego completado")).toBeNull();
  });

  it("asks for 1 to 6 Pokémon before saving", async () => {
    renderApp("/hall-of-fame");
    await journey();

    const form = await record("Verde Hoja", "2026-10-01");
    const save = form.getByRole("button", { name: "Guardar" });
    expect(save).toBeDisabled();
    expect(form.getByText("Añade de 1 a 6 Pokémon.")).toBeVisible();

    for (const name of ["Gengar", "Gastly", "Haunter", "Onix", "Geodude", "Staryu"]) {
      await userEvent.type(
        form.getByRole("searchbox", { name: "Añadir un Pokémon al equipo" }),
        name,
      );
      await userEvent.click(await form.findByRole("button", { name: `Añadir ${name}` }));
    }
    expect(form.getByText("Equipo en orden (6 de 6)")).toBeVisible();
    expect(form.getByRole("searchbox", { name: "Añadir un Pokémon al equipo" })).toBeDisabled();
    expect(save).toBeEnabled();
  });

  it("correcting the date reorders the journey and moves the last game", async () => {
    renderApp("/hall-of-fame");
    await journey();
    const form = await record("Verde Hoja", "2026-10-01", "Gengar");
    await userEvent.click(form.getByRole("button", { name: "Guardar" }));
    await vi.waitFor(async () => {
      expect(await journey()).toHaveLength(2);
    });
    const leafgreen = within(screen.getByRole("listitem", { name: /Verde Hoja/ }));
    expect(leafgreen.getByText("Último juego completado")).toBeVisible();

    await userEvent.click(leafgreen.getByRole("button", { name: "Corregir" }));
    const edit = within(screen.getByRole("form", { name: /Corregir: Verde Hoja/ }));
    const date = edit.getByLabelText("Fecha");
    await userEvent.clear(date);
    await userEvent.type(date, "2026-03-01");
    await userEvent.click(edit.getByRole("button", { name: "Guardar" }));

    await vi.waitFor(async () => {
      expect(await journey()).toEqual([
        "Verde Hoja, 1 de marzo de 2026",
        "Rojo Fuego, 20 de septiembre de 2026",
      ]);
    });
    expect(
      within(screen.getByRole("listitem", { name: /Rojo Fuego/ })).getByText(
        "Último juego completado",
      ),
    ).toBeVisible();
  });

  it("removes an entry only after confirming", async () => {
    renderApp("/hall-of-fame");
    const entry = within(await screen.findByRole("listitem", { name: /Rojo Fuego/ }));

    await userEvent.click(entry.getByRole("button", { name: "Eliminar" }));
    const confirm = within(entry.getByRole("alertdialog", { name: "Confirmar la eliminación" }));
    await userEvent.click(confirm.getByRole("button", { name: "Cancelar" }));
    expect(screen.getByRole("listitem", { name: /Rojo Fuego/ })).toBeVisible();

    await userEvent.click(entry.getByRole("button", { name: "Eliminar" }));
    await userEvent.click(entry.getByRole("button", { name: "Sí, eliminar" }));
    expect(
      await screen.findByText("Todavía no has registrado ningún juego completado."),
    ).toBeVisible();
  });

  it("filters by game and keeps the filter in the URL", async () => {
    renderApp("/hall-of-fame");
    await journey();

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Juego" }), "Verde Hoja");

    expect(currentLocation()).toBe("/hall-of-fame?game=leafgreen");
    expect(await screen.findByText("No hay ningún registro de este juego.")).toBeVisible();
  });

  it("shows the 422 of the API next to the form and keeps it open", async () => {
    server.use(
      http.post("/api/hall-of-fame", () =>
        HttpResponse.json(
          { detail: "Pokémon que no existen en la 1.ª generación: dragonite" },
          { status: 422 },
        ),
      ),
    );
    renderApp("/hall-of-fame");
    await journey();
    const form = await record("Rojo", "2026-01-15", "Dragonite");

    await userEvent.click(form.getByRole("button", { name: "Guardar" }));

    expect(await form.findByRole("alert")).toHaveTextContent(
      "Pokémon que no existen en la 1.ª generación: dragonite",
    );
    expect(screen.getByRole("form", { name: "Registrar un equipo" })).toBeVisible();
    expect(await journey()).toHaveLength(1);
  });
});
