/**
 * Search box to choose a Pokémon by name, for the teams of the key battles and of the Hall of
 * Fame. It shows the first matches of the catalogue; the API validates the choice.
 */
import { useState } from "react";

import { usePokemonSearch } from "../api/queries/pokemon";
import type { CatalogPokemon } from "../api/types";
import { formatDexNumber } from "../lib/format";
import ErrorMessage from "./ErrorMessage";
import { TypeBadges } from "./TypeBadge";

const MAX_RESULTS = 8;

interface Props {
  label: string;
  onPick: (pokemon: CatalogPokemon) => void;
  disabled?: boolean;
}

export default function PokemonPicker({ label, onPick, disabled = false }: Props) {
  const [q, setQ] = useState("");
  const search = usePokemonSearch(q);
  const found = q.trim() === "" ? [] : (search.data?.pokemon ?? []);

  return (
    <div className="space-y-2">
      <label className="flex flex-col text-sm">
        {label}
        <input
          type="search"
          className="rounded border border-slate-300 bg-white px-2 py-1"
          value={q}
          disabled={disabled}
          placeholder="Escribe parte del nombre"
          onChange={(event) => {
            setQ(event.target.value);
          }}
        />
      </label>
      {search.error !== null && <ErrorMessage error={search.error} />}
      {q.trim() !== "" && search.data !== undefined && found.length === 0 && (
        <p className="text-sm text-slate-600">Ningún Pokémon coincide.</p>
      )}
      {found.length > 0 && (
        <ul aria-label="Resultados de la búsqueda" className="space-y-1">
          {found.slice(0, MAX_RESULTS).map((pokemon) => (
            <li key={pokemon.pokemon} className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                disabled={disabled}
                className="rounded border border-slate-300 bg-white px-2 py-0.5 text-sm hover:border-red-700 disabled:opacity-50"
                onClick={() => {
                  onPick(pokemon);
                  setQ("");
                }}
              >
                {`Añadir ${pokemon.name}`}
              </button>
              <span className="font-mono text-xs text-slate-500">
                {formatDexNumber(pokemon.dex_number)}
              </span>
              <TypeBadges types={pokemon.types} />
            </li>
          ))}
        </ul>
      )}
      {found.length > MAX_RESULTS && (
        <p className="text-sm text-slate-600">
          {`Y ${String(found.length - MAX_RESULTS)} más: escribe más letras para afinar.`}
        </p>
      )}
    </div>
  );
}
