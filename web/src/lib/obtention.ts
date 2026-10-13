/**
 * The ways of obtaining a Pokémon (docs/01-ddf/reglas-negocio.md, RN-24 to RN-26) in Spanish
 * text, as the DDF shows them: «Regalo en Ciudad Azulona», «Aparece salvaje en la Ruta 29
 * (noche): 50 %», «Pokémon errante si elegiste a Squirtle». The API decides the ways and their
 * order; this module only words them. A condition or item it does not know is shown with its
 * PokeAPI identifier, never hidden.
 */
import type { ObtentionMethod, ObtentionWay } from "../api/types";
import { describeMethod } from "./evolution";

/** Fossils and items of the loaded generations (1 to 4), with their article: «el Fósil Domo». */
export const ITEMS: Readonly<Record<string, string>> = {
  "helix-fossil": "el Fósil Hélice",
  "dome-fossil": "el Fósil Domo",
  "old-amber": "el Ámbar Viejo",
  "root-fossil": "el Fósil Raíz",
  "claw-fossil": "el Fósil Garra",
  "skull-fossil": "el Fósil Cráneo",
  "armor-fossil": "el Fósil Coraza",
  mysticticket: "el Ticket Misterioso",
  auroraticket: "el Ticket Aurora",
  "eon-ticket": "el Ticket Eón",
  "old-sea-map": "el Mapa Viejo Mar",
  "member-card": "el Carné de Socio",
  "oaks-letter": "la Carta del Profesor Oak",
  "azure-flute": "la Flauta Azur",
  "adamant-orb": "la Diamansfera",
  "lustrous-orb": "la Lustresfera",
  "odd-keystone": "la Piedra Espíritu",
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
  headbutt: "con Cabezazo",
  "honey-tree": "en los árboles de miel",
};

const WEEKDAYS: Readonly<Record<string, string>> = {
  monday: "lunes",
  tuesday: "martes",
  wednesday: "miércoles",
  thursday: "jueves",
  friday: "viernes",
  saturday: "sábados",
  sunday: "domingos",
};

const GBA_GAMES: Readonly<Record<string, string>> = {
  ruby: "Rubí",
  sapphire: "Zafiro",
  emerald: "Esmeralda",
  firered: "Rojo Fuego",
  leafgreen: "Verde Hoja",
};

/** The zones of the Safari Zone of HeartGold and SoulSilver, by the objects placed in them. */
const SAFARI_OBJECTS: Readonly<Record<string, string>> = {
  forest: "bosque",
  plains: "llanura",
  peak: "montaña",
  water: "agua",
};

/** Conditions of the 4th generation with a fixed text. */
const CONDITIONS: Readonly<Record<string, string>> = {
  "first-party-pokemon-high-friendship": "con mucha amistad con el primer Pokémon del equipo",
  "other-virtual-console": "en la consola virtual",
  "radar-on": "con el Pokéradar",
  "radio-hoenn": "con el sonido de Hoenn en la radio",
  "radio-sinnoh": "con el sonido de Sinnoh en la radio",
  "headbutt-tree-rare": "en árboles poco frecuentes",
  "headbutt-tree-secret": "en árboles especiales",
  "bug-catching-contest-yes": "en el Concurso de Captura de Bichos",
  "backlot-mentioned": "el día que lo menciona el dueño del Jardín Trofeo",
  "other-correct-password": "con la contraseña correcta",
  "other-received-kanto-starter": "tras recibir un inicial de Kanto",
  "other-event-arceus-in-party": "con un Arceus de evento en el equipo",
  "other-regirock-regice-registeel-in-party": "con Regirock, Regice y Registeel en el equipo",
  "other-snorlax-11-beat-league": "tras ganar la Liga",
  "other-talk-to-cynthias-grandmother": "tras hablar con la abuela de Cintia",
  "other-talked-to-32-people-underground": "tras hablar con 32 personas en el Subsuelo",
  "other-giratina-not-caught-in-distortion-world":
    "si no capturaste a Giratina en el Mundo Distorsión",
};

const TV_OPTIONS: Readonly<Record<string, string>> = { red: "rojo", blue: "azul" };

/** A PokeAPI identifier as a name, when the API gives no name: `nidoran-f` → «Nidoran f». */
function fromSlug(slug: string): string {
  const text = slug.replaceAll("-", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function itemName(item: string): string {
  return ITEMS[item] ?? `el ${item}`;
}

/** A condition as text, or its PokeAPI identifier if it has none. */
function conditionText(condition: string): string {
  const fixed = CONDITIONS[condition];
  if (fixed !== undefined) return fixed;
  let match = /^weekday-(\w+)$/.exec(condition);
  if (match) return `los ${WEEKDAYS[match[1] ?? ""] ?? match[1] ?? ""}`;
  match = /^slot2-(\w+)$/.exec(condition);
  if (match) return `con ${GBA_GAMES[match[1] ?? ""] ?? match[1] ?? ""} en la ranura de GBA`;
  match = /^honey-tree-group-(\w)$/.exec(condition);
  if (match) return `grupo ${(match[1] ?? "").toUpperCase()} de los árboles de miel`;
  match = /^great-marsh-daily-slot-\d+-of-32$/.exec(condition);
  if (match) return "solo algunos días";
  match = /^johto-safari-blocks-(\w+)-min-(\d+)$/.exec(condition);
  if (match) {
    const zone = SAFARI_OBJECTS[match[1] ?? ""] ?? match[1] ?? "";
    return `con ${match[2] ?? ""} objetos de ${zone} o más en la zona`;
  }
  match = /^item-(.+)$/.exec(condition);
  if (match) return `con ${itemName(match[1] ?? "")}`;
  return condition;
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
    .map(conditionText);
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
      text = `Revivir ${way.item === null ? "el fósil" : itemName(way.item)} en ${place}`;
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
      text = way.item === null ? `Evento: ${place}` : `Evento: ${place} con ${itemName(way.item)}`;
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
