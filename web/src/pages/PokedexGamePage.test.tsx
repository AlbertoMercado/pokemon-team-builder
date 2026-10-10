import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { renderApp } from "../test/render";
import { startPokedex } from "../test/pokedex";

async function objective() {
  return within(await screen.findByRole("region", { name: "Pokémon objetivo" }));
}

describe("Pokédex de un juego: la lista inicial (RF-21)", () => {
  it("marks those already registered, confirms and goes on to the objective", async () => {
    renderApp("/pokedex/leafgreen");

    const list = within(await screen.findByRole("region", { name: "Lista inicial" }));
    await userEvent.type(list.getByRole("searchbox", { name: "Buscar por nombre" }), "saur");
    expect(list.queryByText("Pikachu")).not.toBeInTheDocument();
    await userEvent.click(list.getByRole("checkbox", { name: /Bulbasaur/ }));
    await userEvent.clear(list.getByRole("searchbox", { name: "Buscar por nombre" }));
    await userEvent.click(list.getByRole("checkbox", { name: /Pikachu/ }));
    await userEvent.click(list.getByRole("button", { name: "Confirmar (2 registrados)" }));

    const card = await objective();
    expect(card.getByRole("heading", { name: "Ivysaur" })).toBeVisible();
    expect(card.getByText("Evolucionar Bulbasaur: Nivel 16")).toBeVisible();
    expect(screen.getByText(/2 de 6 registrados · En curso/)).toBeVisible();
    expect(screen.queryByRole("region", { name: "Lista inicial" })).not.toBeInTheDocument();
  });
});

describe("Pokédex de un juego: el Pokémon objetivo (RF-22, RN-23)", () => {
  it("shows the simplest way and, once registered, the next one", async () => {
    startPokedex("leafgreen");
    renderApp("/pokedex/leafgreen");

    let card = await objective();
    expect(card.getByRole("heading", { name: "Bulbasaur" })).toBeVisible();
    expect(card.getByText("La forma más sencilla")).toBeVisible();
    expect(card.getByText("Regalo en Pueblo Paleta si lo elegiste como inicial")).toBeVisible();
    await userEvent.click(card.getByRole("button", { name: "Registrado" }));

    card = await objective();
    expect(await card.findByRole("heading", { name: "Ivysaur" })).toBeVisible();
  });

  it("links to the card of the Pokémon to evolve if it is not registered (CA-76)", async () => {
    startPokedex("leafgreen");
    renderApp("/pokedex/leafgreen");

    await userEvent.click((await objective()).getByRole("button", { name: "Saltar de momento" }));
    const card = await objective();
    expect(await card.findByRole("heading", { name: "Ivysaur" })).toBeVisible();
    expect(card.getByRole("link", { name: "Cómo obtener Bulbasaur" })).toHaveAttribute(
      "href",
      "/pokedex/leafgreen/pokemon/bulbasaur",
    );
  });

  it("does not keep the skipped ones: on coming back, the first one again (CA-77)", async () => {
    startPokedex("leafgreen");
    renderApp("/pokedex/leafgreen");
    await userEvent.click((await objective()).getByRole("button", { name: "Saltar de momento" }));
    expect(await (await objective()).findByRole("heading", { name: "Ivysaur" })).toBeVisible();

    await userEvent.click(screen.getByRole("link", { name: "Volver a las Pokédex" }));
    await userEvent.click(await screen.findByRole("link", { name: "Verde Hoja" }));
    expect(await (await objective()).findByRole("heading", { name: "Bulbasaur" })).toBeVisible();
  });

  it("chooses another way, keeps it marked and goes back to the recommended one (RF-23)", async () => {
    startPokedex("leafgreen", "bulbasaur", "ivysaur");
    renderApp("/pokedex/leafgreen");

    const card = await objective();
    expect(await card.findByRole("heading", { name: "Pikachu" })).toBeVisible();
    expect(card.getByText("Aparece salvaje en Bosque Verde: 5 %")).toBeVisible();
    await userEvent.click(card.getByRole("button", { name: "Otras formas de obtenerlo" }));
    const ways = within(card.getByRole("list", { name: "Formas de obtenerlo" }));
    expect(ways.getByText("Recomendada")).toBeVisible();
    await userEvent.click(ways.getByRole("button", { name: "Elegir esta" }));

    expect(await card.findByText("Elegida por ti", { selector: "p" })).toBeVisible();
    expect(
      card.getAllByText("Transferirlo desde Rojo Fuego: Aparece salvaje en Bosque Verde: 5 %")[0],
    ).toBeVisible();
    await userEvent.click(card.getByRole("button", { name: "Volver a la recomendada" }));
    expect(await card.findByText("La forma más sencilla")).toBeVisible();
  });

  it("marks one as impossible and counts it apart (RN-22)", async () => {
    startPokedex("leafgreen", "bulbasaur", "ivysaur", "pikachu", "sandshrew");
    renderApp("/pokedex/leafgreen");

    const card = await objective();
    expect(await card.findByRole("heading", { name: "Mew" })).toBeVisible();
    expect(card.getByText("Pokémon obtenido por evento")).toBeVisible();
    await userEvent.click(card.getByRole("button", { name: "Imposible de obtener" }));

    expect(
      await screen.findByText(
        "No queda ninguno por registrar: los que faltan son imposibles de obtener.",
      ),
    ).toBeVisible();
    expect(screen.getByText(/4 de 6 registrados · En curso · 2 imposibles/)).toBeVisible();
  });

  it("says when every one left has been skipped, and starts again", async () => {
    startPokedex("leafgreen", "bulbasaur", "ivysaur", "pikachu", "sandshrew");
    renderApp("/pokedex/leafgreen");
    await (await objective()).findByRole("heading", { name: "Mew" });
    await userEvent.click((await objective()).getByRole("button", { name: "Saltar de momento" }));

    await userEvent.click(await screen.findByRole("button", { name: "Volver al primero" }));
    expect(await (await objective()).findByRole("heading", { name: "Mew" })).toBeVisible();
  });

  it("shows the 404 of a game that is not in the Hall of Fame", async () => {
    renderApp("/pokedex/firered");
    expect(await screen.findByRole("alert")).toHaveTextContent("no está en el Hall of Fame");
    expect(screen.getByRole("link", { name: "Volver a las Pokédex" })).toBeVisible();
  });
});
