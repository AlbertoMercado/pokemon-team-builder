import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { renderApp } from "../test/render";
import { server, withoutCovers } from "../test/server";

const card = (name: string) => screen.getByRole("listitem", { name });

/** The cover next to the main heading, if any. */
function headerCover(): string | null {
  const heading = screen.getByRole("heading", { level: 1 });
  return heading.parentElement?.querySelector("img")?.getAttribute("src") ?? null;
}

describe("Revisión de datos", () => {
  it("groups the data to confirm and warns about the responsibility (RF-15)", async () => {
    renderApp("/juego/firered/revision");

    expect(await screen.findByText("Faltan 5 datos por confirmar.")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent("Los datos que confirmas se usan tal cual");
    expect(
      screen.getAllByRole("heading", { level: 2 }).map((heading) => heading.textContent),
    ).toEqual(["Mecánicas del juego", "Combates clave", "Favoritos"]);
    expect(within(card("Concursos")).getByText("¿Rojo Fuego tiene esta mecánica?")).toBeVisible();
    expect(screen.queryByRole("link", { name: "Generar el equipo" })).not.toBeInTheDocument();
  });

  it("accepts the proposals, fills in the pending one and opens the result (RN-18)", async () => {
    renderApp("/juego/firered/revision");

    const raichu = await screen.findByRole("listitem", { name: "Raichu" });
    expect(
      within(raichu).getByText(
        "¿Puede llegar a Rojo Fuego y evolucionar hasta Raichu antes de completarlo?",
      ),
    ).toBeVisible();
    expect(within(raichu).getByText("Propuesta: No.")).toBeVisible();

    await userEvent.click(screen.getByRole("button", { name: "Aceptar todas las propuestas" }));
    expect(await screen.findByText("Falta 1 dato por confirmar.")).toBeInTheDocument();
    expect(within(card("Raichu")).getByText("Confirmado")).toBeVisible();
    expect(within(card("Raichu")).getByRole("button", { name: "No" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(
      screen.queryByRole("button", { name: "Aceptar todas las propuestas" }),
    ).not.toBeInTheDocument();

    // Misty has no proposal: her team is filled in with the picker.
    const misty = card("Equipo de Misty");
    expect(within(misty).getByText("Sin propuesta: indica tú su equipo.")).toBeVisible();
    await userEvent.click(within(misty).getByRole("button", { name: "Indicar el equipo" }));
    const search = within(misty).getByRole("searchbox", { name: "Añadir un Pokémon al equipo" });
    await userEvent.type(search, "star");
    await userEvent.click(await within(misty).findByRole("button", { name: "Añadir Staryu" }));
    await userEvent.type(search, "starm");
    await userEvent.click(await within(misty).findByRole("button", { name: "Añadir Starmie" }));
    await userEvent.click(within(misty).getByRole("button", { name: "Guardar el equipo" }));

    expect(await screen.findByText("Todos los datos están confirmados.")).toBeInTheDocument();
    const team = within(card("Equipo de Misty")).getByRole("list", { name: "Equipo" });
    expect(
      within(team)
        .getAllByRole("listitem")
        .map((item) => item.textContent),
    ).toEqual(["Staryu", "Starmie"]);
    expect(screen.getByRole("link", { name: "Generar el equipo" })).toHaveAttribute(
      "href",
      "/juego/firered/resultado",
    );
  });

  it("corrects a fact one by one", async () => {
    renderApp("/juego/firered/revision");
    const raichu = await screen.findByRole("listitem", { name: "Raichu" });

    await userEvent.click(within(raichu).getByRole("button", { name: "Sí" }));

    expect(await within(raichu).findByText("Confirmado")).toBeVisible();
    expect(within(raichu).getByRole("button", { name: "Sí" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(await screen.findByText("Faltan 4 datos por confirmar.")).toBeInTheDocument();
  });

  it("points out a confirmation that a new load made outdated", async () => {
    renderApp("/juego/firered/revision");
    const lapras = await screen.findByRole("listitem", { name: "Lapras" });

    expect(within(lapras).getByText("Desactualizado")).toBeVisible();
    expect(
      within(lapras).getByText(/Lo confirmaste como «Sí», pero la carga actual propone otra cosa/),
    ).toBeVisible();
    expect(within(lapras).getByRole("button", { name: "Sí" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("corrects the proposed team of a key battle", async () => {
    renderApp("/juego/firered/revision");
    const brock = await screen.findByRole("listitem", { name: "Equipo de Brock" });
    // The names arrive with the catalogue; until then, the identifiers.
    await vi.waitFor(() => {
      expect(
        within(within(brock).getByRole("list", { name: "Equipo" }))
          .getAllByRole("listitem")
          .map((item) => item.textContent),
      ).toEqual(["Geodude", "Onix"]);
    });

    await userEvent.click(within(brock).getByRole("button", { name: "Corregir el equipo" }));
    await userEvent.click(within(brock).getByRole("button", { name: "Quitar Geodude" }));
    await userEvent.type(
      within(brock).getByRole("searchbox", { name: "Añadir un Pokémon al equipo" }),
      "geo",
    );
    await userEvent.click(await within(brock).findByRole("button", { name: "Añadir Geodude" }));
    await userEvent.click(within(brock).getByRole("button", { name: "Guardar el equipo" }));

    const confirmed = await within(card("Equipo de Brock")).findByText("Equipo confirmado:");
    expect(confirmed).toBeVisible();
    const team = within(card("Equipo de Brock")).getByRole("list", { name: "Equipo" });
    expect(
      within(team)
        .getAllByRole("listitem")
        .map((item) => item.textContent),
    ).toEqual(["Onix", "Geodude"]);
  });

  it("shows the 422 of a Pokémon that does not exist and keeps the team to fix it", async () => {
    server.use(
      http.put("/api/games/firered/review/:fact_key", () =>
        HttpResponse.json(
          { detail: "Pokémon que no existen en la 3.ª generación: onix-mega" },
          { status: 422 },
        ),
      ),
    );
    renderApp("/juego/firered/revision");
    const brock = await screen.findByRole("listitem", { name: "Equipo de Brock" });

    await userEvent.click(within(brock).getByRole("button", { name: "Corregir el equipo" }));
    await userEvent.click(within(brock).getByRole("button", { name: "Guardar el equipo" }));

    expect(await within(brock).findByRole("alert")).toHaveTextContent(
      "Pokémon que no existen en la 3.ª generación: onix-mega",
    );
    expect(within(brock).getByRole("list", { name: "Equipo corregido" })).toBeVisible();
  });

  it("explains that a game is not a target game (404)", async () => {
    renderApp("/juego/red/revision");
    expect(await screen.findByRole("alert")).toHaveTextContent("red no es un juego objetivo");
  });
});

describe("Portada y fuentes en la revisión (RF-18, ADR-0004)", () => {
  it("shows the cover of the game in the header", async () => {
    renderApp("/juego/firered/revision");
    await screen.findByText("Faltan 5 datos por confirmar.");

    expect(headerCover()).toBe("/api/games/firered/cover");
  });

  it("shows only the name of the game without cover", async () => {
    withoutCovers();
    renderApp("/juego/firered/revision");
    await screen.findByText("Faltan 5 datos por confirmar.");

    expect(headerCover()).toBeNull();
    expect(
      screen.getByRole("heading", { level: 1, name: "Revisión de datos: Rojo Fuego" }),
    ).toBeVisible();
  });

  it("links a key battle to the WikiDex revision its team comes from", async () => {
    renderApp("/juego/firered/revision");
    await screen.findByText("Faltan 5 datos por confirmar.");

    expect(within(card("Equipo de Brock")).getByRole("link", { name: "WikiDex" })).toHaveAttribute(
      "href",
      "https://www.wikidex.net/index.php?title=Brock&oldid=3562807",
    );
    // Misty has no known source.
    expect(within(card("Equipo de Misty")).queryByRole("link")).not.toBeInTheDocument();
  });
});
