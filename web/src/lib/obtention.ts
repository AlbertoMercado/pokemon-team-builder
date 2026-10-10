/**
 * The ways of obtaining a Pokémon (docs/01-ddf/reglas-negocio.md, RN-24 to RN-26) in Spanish
 * text, as the DDF shows them: «Regalo en Ciudad Azulona», «Aparece salvaje en la Ruta 29
 * (noche): 50 %», «Pokémon errante si elegiste a Squirtle». The API decides the ways and their
 * order; this module only words them. A condition or item it does not know is shown with its
 * PokeAPI identifier, never hidden.
 */
import type { ObtentionMethod, ObtentionWay } from "../api/types";
import { describeMethod } from "./evolution";

/** Fossils and event items of the loaded generations (1 to 3). */
export const ITEMS: Readonly<Record<string, string>> = {
  "helix-fossil": "Fósil Hélice",
  "dome-fossil": "Fósil Domo",
  "old-amber": "Ámbar Viejo",
  "root-fossil": "Fósil Raíz",
  "claw-fossil": "Fósil Garra",
  mysticticket: "Ticket Misterioso",
  auroraticket: "Ticket Aurora",
  "eon-ticket": "Ticket Eón",
  "old-sea-map": "Mapa Viejo Mar",
};

const TIMES: Readonly<Record<string, string>> = {
  morning: "mañana",
  day: "día",
  night: "noche",
};

/** How it is met when it is not walking: «surfeando», «con la Supercaña». */
const WILD_METHODS: Readonly<Record<string, string>> = {
  surf: "surfeando",
  seaweed: "buceando",
  "old-rod": "con la Caña Vieja",
  "good-rod": "con la Caña Buena",
  "super-rod": "con la Supercaña",
  "feebas-tile-fishing": "pescando en sus casillas",
  "rock-smash": "con Golpe Roca",
  "headbutt-low": "con Cabezazo",
  "headbutt-normal": "con Cabezazo",
  "headbutt-high": "con Cabezazo",
};

const TV_OPTIONS: Readonly<Record<string, string>> = { red: "rojo", blue: "azul" };

/** A PokeAPI identifier as a name, when the API gives no name: `nidoran-f` → «Nidoran f». */
function fromSlug(slug: string): string {
  const text = slug.replaceAll("-", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function itemName(item: string): string {
  return ITEMS[item] ?? item;
}

/** «A», «A y B», «A, B y C». */
function list(names: readonly string[]): string {
  return names.length <= 1
    ? (names[0] ?? "")
    : `${names.slice(0, -1).join(", ")} y ${names.at(-1) ?? ""}`;
}

/** What depends on a choice: «si elegiste a Squirtle», «si elegiste rojo en la televisión». */
function choiceText(choice: string, species: string, names: Readonly<Record<string, string>>) {
  if (choice.startsWith("starter-")) {
    const starter = choice.slice("starter-".length);
    return starter === species
      ? "si lo elegiste como inicial"
      : `si elegiste a ${names[starter] ?? fromSlug(starter)}`;
  }
  if (choice.startsWith("tv-option-")) {
    const option = choice.slice("tv-option-".length);
    return `si elegiste ${TV_OPTIONS[option] ?? option} en la televisión`;
  }
  return choice;
}

/** The conditions shown with the way (CA-85), without the casino coins and the NPC's Pokémon. */
function extraConditions(conditions: readonly string[]): string[] {
  return conditions
    .filter((c) => !c.startsWith("coins-") && !c.startsWith("trade-"))
    .map((c) => {
      if (c === "weekday-friday") return "los viernes";
      if (c === "first-party-pokemon-high-friendship") {
        return "con mucha amistad con el primer Pokémon del equipo";
      }
      if (c === "other-virtual-console") return "en la consola virtual";
      return c;
    });
}

/**
 * A way of obtaining `species` from the encounters of a game (RN-26). `names` are the Spanish
 * names of the species it may mention (the starter of a choice), by identifier.
 */
export function describeWay(
  way: ObtentionWay,
  species: string,
  names: Readonly<Record<string, string>> = {},
): string {
  const place = way.location_name;
  // Where it appears, the moment and the other conditions go before the probability:
  // «Aparece salvaje en la Cueva Unión (los viernes): 100 %».
  const notes = [...way.times.map((t) => TIMES[t] ?? t), ...extraConditions(way.conditions)];
  const when = notes.length > 0 ? ` (${notes.join(", ")})` : "";
  const appears = way.kind === "static" || way.kind === "wild" || way.kind === "swarm";
  const coins = way.conditions.find((c) => c.startsWith("coins-"));
  const traded = way.conditions.find((c) => c.startsWith("trade-"));
  const choice = way.choice === null ? null : choiceText(way.choice, species, names);
  let text: string;
  switch (way.kind) {
    case "gift":
      text =
        coins === undefined
          ? `Regalo en ${place}`
          : `Premio del casino en ${place} por ${coins.slice("coins-".length)} fichas`;
      if (way.alternatives.length > 0) {
        const all = [names[species] ?? fromSlug(species), ...way.alternatives.map((a) => a.name)];
        text += `, a elegir entre ${list(all)}`;
      }
      break;
    case "npc_trade":
      text = `Intercambiar con un PNJ en ${place}`;
      if (traded !== undefined) text += ` a cambio de ${fromSlug(traded.slice("trade-".length))}`;
      break;
    case "fossil":
      text = `Revivir el ${itemName(way.item ?? "fósil")} en ${place}`;
      break;
    case "static":
      text = `Aparece salvaje en ${place}${when}: 100 %`;
      break;
    case "wild":
    case "swarm": {
      const how = WILD_METHODS[way.method];
      const verb = way.kind === "swarm" ? "Aparece en enjambre" : "Aparece salvaje";
      text = `${verb} en ${place}${how === undefined ? "" : ` ${how}`}${when}: ${String(way.rarity)} %`;
      break;
    }
    case "roaming":
      text = "Pokémon errante";
      break;
    case "starter_gift":
      text = `Regalo en ${place}`;
      break;
    case "event":
      text =
        way.item === null ? `Evento: ${place}` : `Evento: ${place} con el ${itemName(way.item)}`;
      break;
  }
  const extras = [
    ...(choice === null ? [] : [choice]),
    ...(appears ? [] : extraConditions(way.conditions)),
  ];
  return extras.length > 0 ? `${text} ${extras.join(", ")}` : text;
}

/** A way of obtaining `species` (RN-24), with what it starts from. */
export function describeObtention(
  method: ObtentionMethod,
  species: string,
  names: Readonly<Record<string, string>> = {},
): string {
  const from = method.pokemon_name ?? method.pokemon ?? "";
  const incense = method.incense ? ", con un incienso" : "";
  switch (method.kind) {
    case "evolve":
      return method.evolution === null
        ? `Evolucionar ${from}`
        : `Evolucionar ${from}: ${describeMethod(method.evolution)}`;
    case "breed_registered":
      return `Criarlo desde tu ${from}${incense}`;
    case "breed":
      return `Criarlo desde ${from}, que se obtiene en el juego${incense}`;
    case "transfer_registered":
      return `Transferirlo desde ${method.game_name ?? ""}, donde lo tienes registrado`;
    case "transfer":
      return method.way === null
        ? `Transferirlo desde ${method.game_name ?? ""}`
        : `Transferirlo desde ${method.game_name ?? ""}: ${describeWay(method.way, species, names)}`;
    case "in_game":
    case "starter_gift":
      return method.way === null ? method.kind : describeWay(method.way, species, names);
    case "event":
      return method.way === null
        ? "Pokémon obtenido por evento"
        : describeWay(method.way, species, names);
  }
}
