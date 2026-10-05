import { describeMethod, describeMethods } from "./evolution";

describe("describeMethod", () => {
  it.each([
    [{ trigger: "level-up", conditions: { minimum_level: 25 } }, "Nivel 25"],
    [{ trigger: "level-up", conditions: { minimum_happiness: 220 } }, "Amistad alta"],
    [
      { trigger: "level-up", conditions: { minimum_happiness: 160, time_of_day: "day" } },
      "Amistad alta, de día",
    ],
    [
      { trigger: "level-up", conditions: { minimum_happiness: 160, time_of_day: "night" } },
      "Amistad alta, de noche",
    ],
    [{ trigger: "level-up", conditions: { minimum_beauty: 170 } }, "Belleza alta"],
    [
      { trigger: "level-up", conditions: { minimum_level: 20, relative_physical_stats: 1 } },
      "Nivel 20, Ataque mayor que Defensa",
    ],
    [
      { trigger: "level-up", conditions: { minimum_level: 20, relative_physical_stats: -1 } },
      "Nivel 20, Ataque menor que Defensa",
    ],
    [
      { trigger: "level-up", conditions: { minimum_level: 20, relative_physical_stats: 0 } },
      "Nivel 20, Ataque igual a Defensa",
    ],
    [
      {
        trigger: "level-up",
        conditions: {
          minimum_level: 7,
          percentage_chance: 50,
          condition_expression: "PID 16 >> 10 % 4 <=",
        },
      },
      "Nivel 7, al azar (50 %)",
    ],
    [{ trigger: "level-up", conditions: {} }, "Subir de nivel"],
    [{ trigger: "use-item", conditions: { trigger_item: "thunder-stone" } }, "Piedra Trueno"],
    [{ trigger: "use-item", conditions: { trigger_item: "sun-stone" } }, "Piedra Solar"],
    [{ trigger: "trade", conditions: {} }, "Intercambio"],
    [
      { trigger: "trade", conditions: { held_item: "metal-coat" } },
      "Intercambio llevando Revestimiento metálico",
    ],
    [
      { trigger: "trade", conditions: { held_item: "deep-sea-tooth" } },
      "Intercambio llevando Diente Marino",
    ],
    [
      { trigger: "shed", conditions: {} },
      "Aparece al evolucionar Nincada si hay un hueco libre en el equipo y una Poké Ball",
    ],
  ])("describes %j as «%s»", (method, text) => {
    expect(describeMethod(method)).toBe(text);
  });

  it("keeps the identifiers of an unknown trigger, condition or item", () => {
    expect(describeMethod({ trigger: "spin", conditions: {} })).toBe("spin");
    expect(describeMethod({ trigger: "use-item", conditions: { trigger_item: "ice-stone" } })).toBe(
      "ice-stone",
    );
    expect(
      describeMethod({ trigger: "level-up", conditions: { minimum_level: 33, gender: 1 } }),
    ).toBe("Nivel 33, gender: 1");
    expect(describeMethod({ trigger: "level-up", conditions: { time_of_day: "dusk" } })).toBe(
      "Subir de nivel, time_of_day: dusk",
    );
  });

  it("explains the draw of an expression only when there is a chance", () => {
    expect(
      describeMethod({ trigger: "level-up", conditions: { condition_expression: "PID" } }),
    ).toBe("Subir de nivel, condition_expression: PID");
  });
});

describe("describeMethods", () => {
  it("joins alternative methods with «o»", () => {
    expect(
      describeMethods([
        { trigger: "level-up", conditions: { minimum_level: 30 } },
        { trigger: "trade", conditions: {} },
      ]),
    ).toBe("Nivel 30 o Intercambio");
  });
});
