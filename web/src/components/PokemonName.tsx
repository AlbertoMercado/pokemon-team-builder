/** National Pokédex number and name of a form, linked to its detail. */
import { Link } from "react-router";

import { formatDexNumber } from "../lib/format";

interface Props {
  pokemon: string;
  name: string;
  dexNumber: number;
}

export default function PokemonName({ pokemon, name, dexNumber }: Props) {
  return (
    <span className="inline-flex items-baseline gap-2">
      <span className="font-mono text-sm text-slate-500">{formatDexNumber(dexNumber)}</span>
      <Link to={`/pokemon/${pokemon}`} className="font-medium text-slate-900 hover:text-red-700">
        {name}
      </Link>
    </span>
  );
}
