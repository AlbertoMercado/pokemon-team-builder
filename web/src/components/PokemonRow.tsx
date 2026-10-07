/**
 * A row of a list of Pokémon (RF-01, RF-04): its image, number, name and types and, at the
 * right, an optional action such as the favourite star.
 *
 * The row has two zones so that every row of a list is as tall as the others whatever the
 * length of the name or the number of types (#68): at the left, the image and a block with the
 * number and name over the types, in two fixed lines on narrow screens and in one from `sm`;
 * at the right, the action, which never shrinks nor wraps, so the star is always in the same
 * place.
 */
import type { ReactNode } from "react";
import { Link } from "react-router";

import { formatDexNumber } from "../lib/format";
import PokemonSprite from "./PokemonSprite";
import { TypeBadges } from "./TypeBadge";

interface Props {
  pokemon: string;
  name: string;
  dexNumber: number;
  imageUrl: string | null | undefined;
  types: readonly string[];
  /** The form whose detail is being shown: highlighted and marked as the current page. */
  current?: boolean;
  /** Marks after the types, such as the gain of a suggestion. */
  extra?: ReactNode;
  /** At the right of the row, such as the favourite star. */
  action?: ReactNode;
}

export default function PokemonRow({
  pokemon,
  name,
  dexNumber,
  imageUrl,
  types,
  current = false,
  extra,
  action,
}: Props) {
  return (
    <div className="flex items-center gap-3">
      <PokemonSprite url={imageUrl} />
      <div className="flex min-w-0 flex-1 flex-col gap-1 sm:flex-row sm:flex-wrap sm:items-center sm:gap-x-3">
        <span className="flex min-w-0 items-baseline gap-2">
          <span className="font-mono text-sm text-slate-500">{formatDexNumber(dexNumber)}</span>
          <Link
            to={`/pokemon/${pokemon}`}
            aria-current={current ? "page" : undefined}
            className={`truncate ${
              current ? "font-bold text-red-700" : "font-medium text-slate-900 hover:text-red-700"
            }`}
          >
            {name}
          </Link>
        </span>
        <span className="flex flex-wrap items-center gap-2">
          <TypeBadges types={types} />
          {extra}
        </span>
      </div>
      {action !== undefined && <span className="shrink-0">{action}</span>}
    </div>
  );
}
