import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";

import { renderApp } from "../test/render";
import { server } from "../test/server";

const rule = (name: RegExp) => within(screen.getByRole("listitem", { name }));

describe("Reglas (RF-06, RF-07)", () => {
  it("groups the rules by kind with their description and a link to the DDF", async () => {
    renderApp("/reglas");

    const hard = await screen.findByRole("region", { name: "Reglas duras" });
    expect(within(hard).getAllByRole("listitem")).toHaveLength(9);
    expect(screen.getByRole("region", { name: "Reglas de presencia" })).toBeVisible();
    expect(
      within(screen.getByRole("region", { name: "Reglas blandas" })).getAllByRole("listitem"),
    ).toHaveLength(4);
    expect(
      within(screen.getByRole("region", { name: "Mecanismos" })).getAllByRole("listitem"),
    ).toHaveLength(5);
    expect(
      rule(/^RN-12 /).getByText("Ningún tipo aparece en más de un miembro del equipo."),
    ).toBeVisible();
    expect(screen.getByRole("link", { name: "reglas de negocio" })).toHaveAttribute(
      "href",
      expect.stringContaining("docs/01-ddf/reglas-negocio.md") as string,
    );
  });

  it("shows a rule that cannot be configured without a switch", async () => {
    renderApp("/reglas");
    await screen.findByRole("region", { name: "Reglas duras" });

    expect(rule(/^RN-01 /).queryByRole("switch")).toBeNull();
    expect(rule(/^RN-01 /).getByText("Siempre activa")).toBeVisible();
    expect(rule(/^RN-04 /).queryByRole("switch")).toBeNull();
    expect(rule(/^RN-07 /).getByRole("switch", { name: "Activa" })).toBeChecked();
  });

  it("turns a hard rule off and back on", async () => {
    renderApp("/reglas");
    await screen.findByRole("region", { name: "Reglas duras" });

    await userEvent.click(rule(/^RN-12 /).getByRole("switch", { name: "Activa" }));
    await vi.waitFor(() => {
      expect(rule(/^RN-12 /).getByRole("switch", { name: "Activa" })).not.toBeChecked();
    });

    await userEvent.click(rule(/^RN-12 /).getByRole("switch", { name: "Activa" }));
    await vi.waitFor(() => {
      expect(rule(/^RN-12 /).getByRole("switch", { name: "Activa" })).toBeChecked();
    });
  });

  it("changes the weight of a soft rule and keeps its default in sight", async () => {
    renderApp("/reglas");
    await screen.findByRole("region", { name: "Reglas blandas" });
    const weight = rule(/^RN-17 /).getByRole("combobox", { name: /Peso/ });
    expect(weight).toHaveValue("10");
    expect(rule(/^RN-17 /).getByText("(por defecto, 10)")).toBeVisible();

    await userEvent.selectOptions(weight, "4");

    await vi.waitFor(() => {
      expect(rule(/^RN-17 /).getByRole("combobox", { name: /Peso/ })).toHaveValue("4");
    });
    await userEvent.click(rule(/^RN-17 /).getByRole("switch", { name: "Activa" }));
    await vi.waitFor(() => {
      expect(rule(/^RN-17 /).getByRole("switch", { name: "Activa" })).not.toBeChecked();
    });
  });

  it("shows the message of a 409 next to the rule", async () => {
    server.use(
      http.patch("/api/rules/:ruleId", () =>
        HttpResponse.json({ detail: "la regla RN-13 no se puede desactivar" }, { status: 409 }),
      ),
    );
    renderApp("/reglas");
    await screen.findByRole("region", { name: "Reglas de presencia" });

    await userEvent.click(rule(/^RN-13 /).getByRole("switch", { name: "Activa" }));

    expect(await rule(/^RN-13 /).findByRole("alert")).toHaveTextContent(
      "la regla RN-13 no se puede desactivar",
    );
    expect(rule(/^RN-13 /).getByRole("switch", { name: "Activa" })).toBeChecked();
  });
});
