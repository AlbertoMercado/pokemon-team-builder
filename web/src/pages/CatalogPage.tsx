/**
 * Catálogo (RF-01, RF-03): every loaded form with search by name, filters by type and by
 * favourite, all kept in the URL (`?q=`, `?type=`, `?favorite=`), and the star of each one.
 */
import { useSearchParams } from "react-router";

import { useCatalog, type CatalogFilters } from "../api/queries/pokemon";
import ErrorMessage from "../components/ErrorMessage";
import FavoriteButton from "../components/FavoriteButton";
import FavoriteHint from "../components/FavoriteHint";
import PokemonName from "../components/PokemonName";
import { TypeBadges } from "../components/TypeBadge";
import { TYPE_IDS, typeStyle } from "../lib/types";

const FIELD = "rounded border border-slate-300 bg-white px-2 py-1";

function filtersFrom(params: URLSearchParams): CatalogFilters {
  const filters: CatalogFilters = {};
  const q = params.get("q")?.trim();
  if (q) filters.q = q;
  const type = params.get("type");
  if (type) filters.type = type;
  const favorite = params.get("favorite");
  if (favorite === "true" || favorite === "false") filters.favorite = favorite === "true";
  return filters;
}

export default function CatalogPage() {
  const [params, setParams] = useSearchParams();
  const catalog = useCatalog(filtersFrom(params));

  const setParam = (name: string, value: string) => {
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        if (value) {
          next.set(name, value);
        } else {
          next.delete(name);
        }
        return next;
      },
      { replace: true },
    );
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Catálogo</h1>
      <FavoriteHint />
      <form
        role="search"
        className="flex flex-wrap items-end gap-4"
        onSubmit={(event) => {
          event.preventDefault();
        }}
      >
        <label className="flex flex-col text-sm">
          Buscar por nombre
          <input
            type="search"
            className={FIELD}
            value={params.get("q") ?? ""}
            onChange={(event) => {
              setParam("q", event.target.value);
            }}
          />
        </label>
        <label className="flex flex-col text-sm">
          Tipo
          <select
            className={FIELD}
            value={params.get("type") ?? ""}
            onChange={(event) => {
              setParam("type", event.target.value);
            }}
          >
            <option value="">Todos</option>
            {TYPE_IDS.map((type) => (
              <option key={type} value={type}>
                {typeStyle(type).name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-sm">
          Favoritos
          <select
            className={FIELD}
            value={params.get("favorite") ?? ""}
            onChange={(event) => {
              setParam("favorite", event.target.value);
            }}
          >
            <option value="">Todos</option>
            <option value="true">Solo favoritos</option>
            <option value="false">Sin los favoritos</option>
          </select>
        </label>
        {params.size > 0 && (
          <button
            type="button"
            className="text-sm text-red-700 underline"
            onClick={() => {
              setParams({}, { replace: true });
            }}
          >
            Quitar los filtros
          </button>
        )}
      </form>
      <Results query={catalog} />
    </div>
  );
}

function Results({ query }: { query: ReturnType<typeof useCatalog> }) {
  if (query.error !== null) {
    return <ErrorMessage error={query.error} />;
  }
  if (query.data === undefined) {
    return <p className="text-slate-500">Cargando…</p>;
  }
  const { total, pokemon } = query.data;
  return (
    <section aria-label="Resultados">
      <p aria-live="polite" className="mb-2 text-sm text-slate-600">
        {total === 1 ? "1 Pokémon" : `${String(total)} Pokémon`}
      </p>
      {total === 0 ? (
        <p>Ningún Pokémon coincide con la búsqueda.</p>
      ) : (
        <ul aria-label="Pokémon" className="divide-y divide-slate-200 rounded-lg border bg-white">
          {pokemon.map((entry) => (
            <li key={entry.pokemon} className="flex flex-wrap items-center gap-3 px-3 py-2">
              <PokemonName pokemon={entry.pokemon} name={entry.name} dexNumber={entry.dex_number} />
              <TypeBadges types={entry.types} />
              <span className="ml-auto">
                <FavoriteButton
                  pokemon={entry.pokemon}
                  name={entry.name}
                  favorite={entry.favorite}
                />
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
