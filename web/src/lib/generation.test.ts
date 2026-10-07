import type { Discard, Presence } from "../api/types";
import { alternatives, chosenBy, discardSummary, discardsByReason } from "./generation";

const discard = (pokemon: string, reason: Discard["reason"]): Discard => ({
  pokemon,
  name: pokemon,
  rule_id: reason === "breeding" ? "RN-11" : "RN-03",
  reason,
  detail: "",
  fact_key: null,
});

describe("discardSummary", () => {
  it("counts the discards by reason, as RF-10 asks", () => {
    const discards = [
      discard("zapdos", "breeding"),
      discard("pikachu", "arrival"),
      discard("raichu", "arrival"),
      discard("mewtwo", "breeding"),
      discard("chikorita", "generation"),
    ];
    expect(discardSummary(discards, 9)).toBe(
      "De tus 9 favoritos, 1 no existe en la generación del juego, " +
        "2 no pueden llegar y evolucionar antes de completarlo y 2 no se pueden criar.",
    );
  });

  it("writes a single reason without «y»", () => {
    expect(discardSummary([discard("zapdos", "breeding")], 4)).toBe(
      "De tus 4 favoritos, 1 no se puede criar.",
    );
  });

  it("speaks of the only favourite", () => {
    expect(discardSummary([discard("zapdos", "breeding")], 1)).toBe(
      "Tu único favorito no se puede criar.",
    );
  });
});

describe("discardsByReason", () => {
  it("keeps the order of the filters", () => {
    const grouped = discardsByReason([discard("a", "journey"), discard("b", "game")]);
    expect(grouped.map(([reason]) => reason)).toEqual(["game", "journey"]);
  });
});

describe("alternatives", () => {
  it("joins the Pokémon of a position with «o»", () => {
    expect(alternatives(["Magneton"])).toBe("Magneton");
    expect(alternatives(["Cloyster", "Lapras"])).toBe("Cloyster o Lapras");
    expect(alternatives(["Vaporeon", "Jolteon", "Flareon"])).toBe("Vaporeon, Jolteon o Flareon");
  });
});

describe("chosenBy", () => {
  const presence = (rule_id: string, status: Presence["status"], options: string[]): Presence => ({
    rule_id,
    level: 1,
    status,
    options,
    detail: "",
  });

  it("gives the Pokémon that a rule chooses although they are not favourites (CA-65)", () => {
    const chosen = chosenBy([
      presence("RN-13", "candidates", ["dragonite"]),
      presence("RN-14", "reserved", ["vaporeon"]),
      presence("RN-21", "chosen", ["venusaur", "blastoise"]),
    ]);
    expect([...chosen]).toEqual([
      ["venusaur", "RN-21"],
      ["blastoise", "RN-21"],
    ]);
  });
});
