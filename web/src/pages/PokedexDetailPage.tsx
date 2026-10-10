/**
 * The detail of a Pokédex (RF-24): the Pokémon registered and those impossible to obtain, to
 * correct a mistake by unmarking them. Those that are only obtained in spin-offs are impossible
 * on their own (RN-25) and cannot be unmarked. Each one links to its card.
 */
import { Link, useParams } from "react-router";

import { usePokedex, useUnmarkPokemon } from "../api/queries/pokedex";
import type { PokedexSpecies } from "../api/types";
import BackToPokedexes from "../components/BackToPokedexes";
import ErrorMessage from "../components/ErrorMessage";
import PokedexProgress from "../components/PokedexProgress";
import PokemonSprite from "../components/PokemonSprite";
import { formatDexNumber } from "../lib/format";

const SECONDARY =
  "rounded border border-slate-300 bg-white px-3 py-1 text-sm font-medium hover:border-red-700 disabled:cursor-not-allowed disabled:opacity-50";

export default function PokedexDetailPage() {
  const { game = "" } = useParams();
  const pokedex = usePokedex(game);
  const unmark = useUnmarkPokemon(game);
  if (pokedex.error !== null) {
    return (
      <div className="space-y-4">
        <ErrorMessage error={pokedex.error} />
        <BackToPokedexes />
      </div>
    );
  }
  if (pokedex.data === undefined) return <p className="text-slate-500">Cargando…</p>;
  const { species } = pokedex.data;
  const registered = species.filter((s) => s.status === "registered");
  const impossible = species.filter((s) => s.status === "impossible");
  const automatic = species.filter((s) => s.status === null && s.automatically_impossible);

  const row = (entry: PokedexSpecies, canUnmark: boolean) => (
    <li
      key={entry.species}
      className="flex flex-wrap items-center gap-2 rounded border border-slate-200 bg-white px-2 py-1"
    >
      <PokemonSprite url={entry.image_url} />
      <span className="font-mono text-sm text-slate-500">{formatDexNumber(entry.number)}</span>
      <Link
        to={`/pokedex/${game}/pokemon/${entry.species}`}
        className="grow font-medium hover:text-red-700"
      >
        {entry.name}
      </Link>
      {canUnmark && (
        <button
          type="button"
          className={SECONDARY}
          disabled={unmark.isPending}
          aria-label={`Desmarcar ${entry.name}`}
          onClick={() => {
            unmark.mutate(entry.species);
          }}
        >
          Desmarcar
        </button>
      )}
    </li>
  );

  return (
    <div className="space-y-4">
      <Link to={`/pokedex/${game}`} className="text-sm text-red-700 underline">
        Volver a la Pokédex
      </Link>
      <h1 className="text-2xl font-bold">{`Pokédex de ${pokedex.data.game_name}: detalle`}</h1>
      <PokedexProgress progress={pokedex.data.progress} />
      {unmark.error !== null && <ErrorMessage error={unmark.error} />}
      <section className="space-y-2">
        <h2 className="text-lg font-semibold">{`Registrados (${String(registered.length)})`}</h2>
        {registered.length === 0 ? (
          <p className="text-slate-600">Ninguno todavía.</p>
        ) : (
          <ul aria-label="Registrados" className="grid gap-2 sm:grid-cols-2">
            {registered.map((entry) => row(entry, true))}
          </ul>
        )}
      </section>
      <section className="space-y-2">
        <h2 className="text-lg font-semibold">
          {`Imposibles de obtener (${String(impossible.length + automatic.length)})`}
        </h2>
        {impossible.length + automatic.length === 0 ? (
          <p className="text-slate-600">Ninguno.</p>
        ) : (
          <ul aria-label="Imposibles" className="grid gap-2 sm:grid-cols-2">
            {impossible.map((entry) => row(entry, true))}
            {automatic.map((entry) => row(entry, false))}
          </ul>
        )}
        {automatic.length > 0 && (
          <p className="text-sm text-slate-600">
            Los que no se pueden desmarcar solo se obtienen en spin-offs, que no cuentan.
          </p>
        )}
      </section>
    </div>
  );
}
