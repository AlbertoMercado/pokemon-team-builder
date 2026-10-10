import type { ObtentionMethod, ObtentionWay } from "../api/types";
import { describeObtention, describeWay } from "./obtention";

const way = (overrides: Partial<ObtentionWay> & Pick<ObtentionWay, "kind">): ObtentionWay => ({
  location: "celadon-city",
  location_name: "Ciudad Azulona",
  area: null,
  method: "gift",
  rarity: 100,
  times: [],
  choice: null,
  item: null,
  conditions: [],
  alternatives: [],
  ...overrides,
});

const method = (
  overrides: Partial<ObtentionMethod> & Pick<ObtentionMethod, "kind">,
): ObtentionMethod => ({
  key: "key",
  recommended: true,
  chosen: false,
  way: null,
  game: null,
  game_name: null,
  pokemon: null,
  pokemon_name: null,
  pokemon_registered: false,
  evolution: null,
  incense: false,
  ...overrides,
});

describe("Formas de obtenerlo en el juego (RN-26)", () => {
  it.each([
    [way({ kind: "gift" }), "Regalo en Ciudad Azulona"],
    [
      way({ kind: "gift", conditions: ["coins-9999"] }),
      "Premio del casino en Ciudad Azulona por 9999 fichas",
    ],
    [
      way({ kind: "npc_trade", conditions: ["trade-abra"] }),
      "Intercambiar con un PNJ en Ciudad Azulona a cambio de Abra",
    ],
    [
      way({ kind: "fossil", location_name: "Isla Canela", item: "helix-fossil" }),
      "Revivir el Fósil Hélice en Isla Canela",
    ],
    [
      way({ kind: "static", location_name: "Cueva Unión", conditions: ["weekday-friday"] }),
      "Aparece salvaje en Cueva Unión (los viernes): 100 %",
    ],
    [
      way({
        kind: "wild",
        location_name: "la Ruta 29",
        method: "walk",
        rarity: 50,
        times: ["night"],
      }),
      "Aparece salvaje en la Ruta 29 (noche): 50 %",
    ],
    [
      way({ kind: "wild", location_name: "Ruta 119", method: "feebas-tile-fishing", rarity: 50 }),
      "Aparece salvaje en Ruta 119 pescando en sus casillas: 50 %",
    ],
    [
      way({ kind: "swarm", location_name: "Ruta 32", method: "walk", rarity: 40 }),
      "Aparece en enjambre en Ruta 32: 40 %",
    ],
    [
      way({ kind: "roaming", choice: "starter-squirtle" }),
      "Pokémon errante si elegiste a Squirtle",
    ],
    [
      way({ kind: "roaming", choice: "tv-option-red" }),
      "Pokémon errante si elegiste rojo en la televisión",
    ],
    [
      way({ kind: "event", location_name: "Isla Suprema", item: "auroraticket" }),
      "Evento: Isla Suprema con el Ticket Aurora",
    ],
  ])("%#: «%s»", (found, text) => {
    expect(describeWay(found, "x")).toBe(text);
  });

  it("says among which a gift is chosen (CA-87)", () => {
    const dojo = way({
      kind: "gift",
      location_name: "Ciudad Azafrán",
      alternatives: [{ species: "hitmonchan", name: "Hitmonchan" }],
    });
    expect(describeWay(dojo, "hitmonlee", { hitmonlee: "Hitmonlee" })).toBe(
      "Regalo en Ciudad Azafrán, a elegir entre Hitmonlee y Hitmonchan",
    );
  });

  it("says the starter is a choice made at the start (CA-87)", () => {
    const lab = way({ kind: "starter_gift", location_name: "Pueblo Paleta" });
    expect(describeWay({ ...lab, choice: "starter-bulbasaur" }, "bulbasaur")).toBe(
      "Regalo en Pueblo Paleta si lo elegiste como inicial",
    );
    expect(describeWay({ ...lab, choice: "starter-squirtle" }, "eevee")).toBe(
      "Regalo en Pueblo Paleta si elegiste a Squirtle",
    );
  });

  it("shows an unknown condition with its identifier", () => {
    expect(describeWay(way({ kind: "gift", conditions: ["moon-phase"] }), "x")).toBe(
      "Regalo en Ciudad Azulona moon-phase",
    );
  });
});

describe("Formas de obtención (RN-24)", () => {
  it.each([
    [
      method({
        kind: "evolve",
        pokemon_name: "Ivysaur",
        evolution: { trigger: "level-up", conditions: { minimum_level: 32 } },
      }),
      "Evolucionar Ivysaur: Nivel 32",
    ],
    [method({ kind: "breed_registered", pokemon_name: "Pikachu" }), "Criarlo desde tu Pikachu"],
    [
      method({ kind: "breed", pokemon_name: "Marill", incense: true }),
      "Criarlo desde Marill, que se obtiene en el juego, con un incienso",
    ],
    [
      method({ kind: "transfer_registered", game_name: "Rojo Fuego" }),
      "Transferirlo desde Rojo Fuego, donde lo tienes registrado",
    ],
    [
      method({
        kind: "transfer",
        game_name: "Verde Hoja",
        way: way({ kind: "wild", location_name: "Ruta 4", method: "walk", rarity: 25 }),
      }),
      "Transferirlo desde Verde Hoja: Aparece salvaje en Ruta 4: 25 %",
    ],
    [method({ kind: "event" }), "Pokémon obtenido por evento"],
  ])("%#: «%s»", (found, text) => {
    expect(describeObtention(found, "x")).toBe(text);
  });
});
