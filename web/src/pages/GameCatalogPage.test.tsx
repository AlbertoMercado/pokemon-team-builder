import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "../test/render";

async function card(name: string): Promise<HTMLElement> {
  return screen.findByRole("listitem", { name });
}

describe("Juegos: el catálogo de juegos (RF-25)", () => {
  it("shows the games by generation, with their platform", async () => {
    renderApp("/juegos");

    const sections = await screen.findAllByRole("heading", { level: 2 });
    expect(sections.map((heading) => heading.textContent)).toEqual([
      "1.ª generación",
      "3.ª generación",
      "4.ª generación",
      "8.ª generación",
    ]);
    const third = screen.getByRole("list", { name: "Juegos de la 3.ª generación" });
    expect(
      within(third)
        .getAllByRole("listitem")
        .map((item) => item.getAttribute("aria-label")),
    ).toEqual(["Rojo Fuego", "Esmeralda"]);
    expect(within(await card("Espada")).getByText("Nintendo Switch")).toBeVisible();
  });

  it("asks whether a game is playable before choosing it, and makes it a target (CA-92)", async () => {
    renderApp("/juegos");
    const firered = await card("Rojo Fuego");

    await userEvent.click(
      within(firered).getByRole("button", { name: "Elegir como juego objetivo" }),
    );
    const question = within(firered).getByRole("group", {
      name: "¿Puedes jugar a Rojo Fuego en un sistema actual?",
    });
    await userEvent.click(within(question).getByRole("button", { name: "Sí" }));

    expect(await within(firered).findByText("Juego objetivo")).toBeVisible();
    expect(within(firered).getByRole("button", { name: "Quitar" })).toBeVisible();
    expect(
      within(firered).getByText(/Has indicado que puedes jugarlo en un sistema actual/),
    ).toBeVisible();
  });

  it("says why a game that is not playable cannot be chosen (CA-92)", async () => {
    renderApp("/juegos");
    const emerald = await card("Esmeralda");

    await userEvent.click(
      within(emerald).getByRole("button", { name: "Elegir como juego objetivo" }),
    );
    await userEvent.click(within(emerald).getByRole("button", { name: "No" }));

    const alert = await within(emerald).findByRole("alert");
    expect(alert).toHaveTextContent("No se puede elegir como juego objetivo");
    expect(alert).toHaveTextContent("No se puede jugar en un sistema actual de Nintendo");
    expect(
      within(emerald).getByText(/Has indicado que no puedes jugarlo en un sistema actual/),
    ).toBeVisible();
  });

  it("says what data a game lacks, without asking when it is known to be playable", async () => {
    renderApp("/juegos");
    const sword = await card("Espada");

    await userEvent.click(
      within(sword).getByRole("button", { name: "Elegir como juego objetivo" }),
    );

    expect(within(sword).queryByRole("group")).toBeNull();
    expect(await within(sword).findByRole("alert")).toHaveTextContent(
      "Su generación todavía no se carga",
    );
  });

  it("says when a game cannot receive a bred Pokémon (CA-29)", async () => {
    renderApp("/juegos");
    const red = await card("Rojo");

    await userEvent.click(within(red).getByRole("button", { name: "Elegir como juego objetivo" }));
    await userEvent.click(within(red).getByRole("button", { name: "Sí" }));

    const alert = await within(red).findByRole("alert");
    expect(alert).toHaveTextContent("No puede recibir un Pokémon criado en otro juego");
    expect(alert).toHaveTextContent("Sus mecánicas");
  });

  it("removes a chosen game", async () => {
    renderApp("/juegos");
    const firered = await card("Rojo Fuego");
    await userEvent.click(
      within(firered).getByRole("button", { name: "Elegir como juego objetivo" }),
    );
    await userEvent.click(within(firered).getByRole("button", { name: "Sí" }));

    await userEvent.click(await within(firered).findByRole("button", { name: "Quitar" }));

    expect(
      await within(firered).findByRole("button", { name: "Elegir como juego objetivo" }),
    ).toBeVisible();
    expect(within(firered).queryByText("Juego objetivo")).toBeNull();
  });

  it("explains a chosen game that is no longer playable (CA-93)", async () => {
    renderApp("/juegos");
    const firered = await card("Rojo Fuego");
    await userEvent.click(
      within(firered).getByRole("button", { name: "Elegir como juego objetivo" }),
    );
    await userEvent.click(within(firered).getByRole("button", { name: "Sí" }));

    await userEvent.click(await within(firered).findByRole("button", { name: "Cambiar" }));

    expect(
      await within(firered).findByText(/Elegido, pero ahora no se puede ofrecer/),
    ).toBeVisible();
    expect(within(firered).getByText(/No se puede jugar en un sistema actual/)).toBeVisible();
  });
});
