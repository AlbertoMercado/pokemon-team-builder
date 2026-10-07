/**
 * Names in Spanish and colours of the 18 types. The API sends types as identifiers (`fire`);
 * they are fixed, so the web keeps them (docs/02-ddt/web.md).
 */

export interface TypeStyle {
  name: string;
  /** Background colour of the badge. */
  background: string;
  /** Text colour with enough contrast on `background`. */
  text: string;
}

const DARK = "#ffffff";
const LIGHT = "#1f2937";

export const TYPES: Readonly<Record<string, TypeStyle>> = {
  normal: { name: "Normal", background: "#9fa19f", text: LIGHT },
  fighting: { name: "Lucha", background: "#c03028", text: DARK },
  flying: { name: "Volador", background: "#81b9ef", text: LIGHT },
  poison: { name: "Veneno", background: "#8f41cb", text: DARK },
  ground: { name: "Tierra", background: "#915121", text: DARK },
  rock: { name: "Roca", background: "#afa981", text: LIGHT },
  bug: { name: "Bicho", background: "#91a119", text: LIGHT },
  ghost: { name: "Fantasma", background: "#704170", text: DARK },
  steel: { name: "Acero", background: "#60a1b8", text: LIGHT },
  fire: { name: "Fuego", background: "#e62829", text: DARK },
  water: { name: "Agua", background: "#2980ef", text: DARK },
  grass: { name: "Planta", background: "#3fa129", text: DARK },
  electric: { name: "Eléctrico", background: "#fac000", text: LIGHT },
  psychic: { name: "Psíquico", background: "#ef4179", text: DARK },
  ice: { name: "Hielo", background: "#3dcef3", text: LIGHT },
  dragon: { name: "Dragón", background: "#5060e1", text: DARK },
  dark: { name: "Siniestro", background: "#50413f", text: DARK },
  fairy: { name: "Hada", background: "#ef70ef", text: LIGHT },
};

/** The type identifiers in the order of the games, for the filters. */
export const TYPE_IDS = Object.keys(TYPES);

/** The style of a type; an unknown one keeps its identifier, never hidden. */
export function typeStyle(type: string): TypeStyle {
  return TYPES[type] ?? { name: type, background: "#e5e7eb", text: LIGHT };
}
