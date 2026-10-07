/**
 * Texts of the result of a generation (RF-08 to RF-10): the reason of an incomplete team, the
 * reasons of the discards and the state of the presence rules. They only describe what the API
 * sends; the web decides nothing.
 */
import type { Discard, Generation, Presence } from "../api/types";

type IncompleteReason = NonNullable<Generation["incomplete_reason"]>;
type DiscardReason = Discard["reason"];

export const INCOMPLETE_REASONS: Readonly<Record<IncompleteReason, string>> = {
  reserved_slot:
    "Una regla de presencia necesita un Pokémon que no está en tus favoritos, así que se le reserva un hueco.",
  not_enough_candidates: "Menos de 6 de tus favoritos cumplen las reglas.",
  no_valid_team: "Hay 6 o más favoritos válidos, pero no 6 que cumplan juntos las reglas.",
};

interface ReasonText {
  /** Heading of the group of discards. */
  title: string;
  /** For the summary, after the number: «2 no se pueden criar». */
  one: string;
  many: string;
}

/** The reasons in the order of the filters (RN-03 by levels, RN-11, RN-16). */
export const DISCARD_REASONS: Readonly<Record<DiscardReason, ReasonText>> = {
  generation: {
    title: "No existen en la generación del juego",
    one: "no existe en la generación del juego",
    many: "no existen en la generación del juego",
  },
  game: {
    title: "No se pueden tener en el juego",
    one: "no se puede tener en el juego",
    many: "no se pueden tener en el juego",
  },
  arrival: {
    title: "No pueden llegar y evolucionar antes de completarlo",
    one: "no puede llegar y evolucionar antes de completarlo",
    many: "no pueden llegar y evolucionar antes de completarlo",
  },
  breeding: {
    title: "No se pueden criar",
    one: "no se puede criar",
    many: "no se pueden criar",
  },
  journey: {
    title: "Ya usados en tu recorrido",
    one: "ya se usó en tu recorrido",
    many: "ya se usaron en tu recorrido",
  },
};

const REASON_ORDER = Object.keys(DISCARD_REASONS) as DiscardReason[];

/** The discards grouped by reason, in the order of the filters. */
export function discardsByReason(discards: readonly Discard[]): [DiscardReason, Discard[]][] {
  const groups = Map.groupBy(discards, (discard) => discard.reason);
  return REASON_ORDER.flatMap((reason) => {
    const found = groups.get(reason);
    return found === undefined ? [] : [[reason, found]];
  });
}

/** «De tus 9 favoritos, 3 no existen en la generación del juego y 1 no se puede criar.» */
export function discardSummary(discards: readonly Discard[], favorites: number): string {
  const [only] = discards;
  if (favorites === 1 && discards.length === 1 && only !== undefined) {
    return `Tu único favorito ${DISCARD_REASONS[only.reason].one}.`;
  }
  const parts = discardsByReason(discards).map(([reason, found]) => {
    const text = DISCARD_REASONS[reason];
    return `${String(found.length)} ${found.length === 1 ? text.one : text.many}`;
  });
  const listed =
    parts.length <= 1 ? parts.join("") : `${parts.slice(0, -1).join(", ")} y ${parts.at(-1) ?? ""}`;
  return `De tus ${String(favorites)} ${favorites === 1 ? "favorito" : "favoritos"}, ${listed}.`;
}

export const PRESENCE_STATUS: Readonly<Record<Presence["status"], string>> = {
  candidates: "Se cumple con tus favoritos",
  chosen: "Se cumple con un Pokémon del juego que no es favorito",
  reserved: "Se reserva un hueco",
  unmet: "No se puede cumplir en este juego",
};

/** The Pokémon that a presence rule puts in the team although they are not favourites
 * (RN-21, CA-65), each with that rule. */
export function chosenBy(presence: readonly Presence[]): ReadonlyMap<string, string> {
  return new Map(
    presence
      .filter((rule) => rule.status === "chosen")
      .flatMap((rule) => rule.options.map((pokemon) => [pokemon, rule.rule_id] as const)),
  );
}

/** «Cloyster o Lapras», «Magneton»: the names that can take a position. */
export function alternatives(names: readonly string[]): string {
  return names.length <= 1
    ? names.join("")
    : `${names.slice(0, -1).join(", ")} o ${names.at(-1) ?? ""}`;
}
