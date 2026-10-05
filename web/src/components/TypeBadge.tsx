/** A type with its Spanish name and colour; `TypeBadges`, the types of a Pokémon in order. */
import { typeStyle } from "../lib/types";

export function TypeBadge({ type }: { type: string }) {
  const { name, background, text } = typeStyle(type);
  return (
    <span
      className="inline-block rounded px-2 py-0.5 text-xs font-semibold uppercase"
      style={{ backgroundColor: background, color: text }}
    >
      {name}
    </span>
  );
}

export function TypeBadges({ types }: { types: readonly string[] }) {
  return (
    <ul aria-label="Tipos" className="flex flex-wrap gap-1">
      {types.map((type) => (
        <li key={type}>
          <TypeBadge type={type} />
        </li>
      ))}
    </ul>
  );
}
