/**
 * Evolution methods of PokeAPI (trigger and conditions, docs/02-ddt/api.md#catalogo) in
 * Spanish text: «Nivel 25», «Intercambio llevando Revestimiento metálico», «Amistad alta, de
 * día». It knows the triggers, conditions and items of the loaded generations; anything else
 * is shown with its PokeAPI identifier, never hidden.
 */

type ConditionValue = string | number | boolean;

export interface EvolutionMethod {
  trigger: string;
  conditions: Readonly<Record<string, ConditionValue>>;
}

/** Evolution items of the loaded generations (1 to 3). */
export const ITEMS: Readonly<Record<string, string>> = {
  "thunder-stone": "Piedra Trueno",
  "moon-stone": "Piedra Lunar",
  "fire-stone": "Piedra Fuego",
  "leaf-stone": "Piedra Hoja",
  "water-stone": "Piedra Agua",
  "sun-stone": "Piedra Solar",
  "kings-rock": "Roca del Rey",
  "metal-coat": "Revestimiento metálico",
  "dragon-scale": "Escama Dragón",
  "up-grade": "Mejora",
  "deep-sea-tooth": "Diente Marino",
  "deep-sea-scale": "Escama Marina",
};

const TIMES_OF_DAY: Readonly<Record<string, string>> = { day: "de día", night: "de noche" };

const PHYSICAL_STATS: Readonly<Record<string, string>> = {
  "1": "Ataque mayor que Defensa",
  "-1": "Ataque menor que Defensa",
  "0": "Ataque igual a Defensa",
};

const SHED = "Aparece al evolucionar Nincada si hay un hueco libre en el equipo y una Poké Ball";

export function itemName(item: ConditionValue): string {
  return ITEMS[String(item)] ?? String(item);
}

/** Every method of an evolution; alternative methods are joined with «o». */
export function describeMethods(methods: readonly EvolutionMethod[]): string {
  return methods.map(describeMethod).join(" o ");
}

export function describeMethod({ trigger, conditions }: EvolutionMethod): string {
  const pending = new Map(Object.entries(conditions));
  const take = (key: string): ConditionValue | undefined => {
    const value = pending.get(key);
    pending.delete(key);
    return value;
  };

  const parts = triggerParts(trigger, take);
  // The held item completes the trigger: «Intercambio llevando Mejora».
  const held = take("held_item");
  if (held !== undefined) {
    parts[0] = `${parts[0] ?? ""} llevando ${itemName(held)}`;
  }

  const time = take("time_of_day");
  if (time !== undefined) parts.push(TIMES_OF_DAY[String(time)] ?? `time_of_day: ${String(time)}`);

  const stats = take("relative_physical_stats");
  if (stats !== undefined) {
    parts.push(PHYSICAL_STATS[String(stats)] ?? `relative_physical_stats: ${String(stats)}`);
  }

  const chance = take("percentage_chance");
  if (chance !== undefined) {
    parts.push(`al azar (${String(chance)} %)`);
    // How the game draws it (from the personality value): explained by the chance.
    take("condition_expression");
  }

  for (const [key, value] of pending) {
    parts.push(`${key}: ${String(value)}`);
  }
  return parts.join(", ");
}

/** The text of the trigger, with the conditions that define it (level, friendship, item). */
function triggerParts(
  trigger: string,
  take: (key: string) => ConditionValue | undefined,
): string[] {
  switch (trigger) {
    case "level-up": {
      const parts: string[] = [];
      const level = take("minimum_level");
      if (level !== undefined) parts.push(`Nivel ${String(level)}`);
      if (take("minimum_happiness") !== undefined) parts.push("Amistad alta");
      if (take("minimum_beauty") !== undefined) parts.push("Belleza alta");
      return parts.length > 0 ? parts : ["Subir de nivel"];
    }
    case "use-item": {
      const item = take("trigger_item");
      return [item === undefined ? "Usar un objeto" : itemName(item)];
    }
    case "trade":
      return ["Intercambio"];
    case "shed":
      return [SHED];
    default:
      return [trigger];
  }
}
