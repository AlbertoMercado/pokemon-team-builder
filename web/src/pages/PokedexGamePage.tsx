/**
 * The Pokédex of a completed game (RF-21, RF-22). The first time, the list of every Pokémon of
 * its Pokédex, to mark those already registered and confirm it. After that, the card of the
 * objective: the first Pokémon neither registered nor impossible (RN-23), with its simplest way
 * of obtaining it. Registering it or marking it as impossible shows the next one; «Saltar de
 * momento» too, but it is only kept in this screen: on coming back, the objective is again the
 * first one left (CA-77). The detail corrects mistakes (RF-24).
 */
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router";

import { useObjective, usePokedex, useStartPokedex } from "../api/queries/pokedex";
import type { Pokedex, PokedexSpecies } from "../api/types";
import BackToPokedexes from "../components/BackToPokedexes";
import ErrorMessage from "../components/ErrorMessage";
import PokedexCard from "../components/PokedexCard";
import PokedexProgress from "../components/PokedexProgress";
import PokemonSprite from "../components/PokemonSprite";
import { TypeBadges } from "../components/TypeBadge";
import { formatDexNumber } from "../lib/format";

const FIELD = "rounded border border-slate-300 bg-white px-2 py-1";
const BUTTON =
  "rounded border px-3 py-1 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50";
const PRIMARY = `${BUTTON} border-red-700 bg-red-700 text-white hover:bg-red-800`;
const SECONDARY = `${BUTTON} border-slate-300 bg-white hover:border-red-700`;

export default function PokedexGamePage() {
  const { game = "" } = useParams();
  const pokedex = usePokedex(game);
  if (pokedex.error !== null) {
    return (
      <div className="space-y-4">
        <ErrorMessage error={pokedex.error} />
        <BackToPokedexes />
      </div>
    );
  }
  if (pokedex.data === undefined) {
    return <p className="text-slate-500">Cargando…</p>;
  }
  const started = pokedex.data.progress.status !== "not_started";
  return (
    <div className="space-y-4">
      <BackToPokedexes />
      <h1 className="text-2xl font-bold">{`Pokédex de ${pokedex.data.game_name}`}</h1>
      <PokedexProgress progress={pokedex.data.progress} />
      {started ? (
        <>
          <Link to={`/pokedex/${game}/detalle`} className="text-sm text-red-700 underline">
            Ver los registrados y los imposibles
          </Link>
          <Objective game={game} completed={pokedex.data.progress.status === "completed"} />
        </>
      ) : (
        <InitialList pokedex={pokedex.data} />
      )}
    </div>
  );
}

/** The first time: mark those already registered and confirm (RF-21). */
function InitialList({ pokedex }: { pokedex: Pokedex }) {
  const start = useStartPokedex(pokedex.game);
  const [marked, setMarked] = useState<ReadonlySet<string>>(new Set());
  const [query, setQuery] = useState("");
  const shown = useMemo(() => {
    const wanted = query.trim().toLocaleLowerCase("es");
    return pokedex.species.filter((s) => s.name.toLocaleLowerCase("es").includes(wanted));
  }, [pokedex.species, query]);
  const toggle = (species: string) => {
    const next = new Set(marked);
    if (!next.delete(species)) next.add(species);
    setMarked(next);
  };

  return (
    <section aria-label="Lista inicial" className="space-y-3">
      <p className="text-slate-700">
        Marca los Pokémon que ya tienes registrados en este juego: capturados u obtenidos, no solo
        vistos. Esta lista solo aparece la primera vez; después podrás corregirla en el detalle.
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col text-sm">
          Buscar por nombre
          <input
            type="search"
            className={FIELD}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
            }}
          />
        </label>
        <button
          type="button"
          className={PRIMARY}
          disabled={start.isPending}
          onClick={() => {
            start.mutate([...marked]);
          }}
        >
          {`Confirmar (${String(marked.size)} registrados)`}
        </button>
      </div>
      {start.error !== null && <ErrorMessage error={start.error} />}
      <ul className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
        {shown.map((species) => (
          <InitialRow
            key={species.species}
            species={species}
            checked={marked.has(species.species)}
            onToggle={toggle}
          />
        ))}
      </ul>
    </section>
  );
}

function InitialRow({
  species,
  checked,
  onToggle,
}: {
  species: PokedexSpecies;
  checked: boolean;
  onToggle: (species: string) => void;
}) {
  return (
    <li>
      <label className="flex flex-wrap items-center gap-2 rounded border border-slate-200 bg-white px-2 py-1">
        <input
          type="checkbox"
          checked={checked}
          onChange={() => {
            onToggle(species.species);
          }}
        />
        <PokemonSprite url={species.image_url} />
        <span className="font-mono text-sm text-slate-500">{formatDexNumber(species.number)}</span>
        <span className="font-medium">{species.name}</span>
        <TypeBadges types={species.types} />
      </label>
    </li>
  );
}

/** The card of the next Pokémon to register; the skipped ones only live here (CA-77). */
function Objective({ game, completed }: { game: string; completed: boolean }) {
  const [skipped, setSkipped] = useState<string[]>([]);
  const objective = useObjective(game, skipped);
  if (objective.error !== null) return <ErrorMessage error={objective.error} />;
  if (objective.data === undefined) return <p className="text-slate-500">Cargando…</p>;
  const pokemon = objective.data.pokemon;
  if (pokemon === null) {
    return skipped.length > 0 ? (
      <div className="space-y-2">
        <p>Has saltado todos los que quedan.</p>
        <button
          type="button"
          className={SECONDARY}
          onClick={() => {
            setSkipped([]);
          }}
        >
          Volver al primero
        </button>
      </div>
    ) : (
      <p className="font-semibold">
        {completed
          ? "¡Pokédex completada! Ya puedes conseguir el diploma."
          : "No queda ninguno por registrar: los que faltan son imposibles de obtener."}
      </p>
    );
  }
  return (
    <section aria-label="Pokémon objetivo" className="space-y-2">
      <h2 className="text-lg font-semibold">Siguiente Pokémon que registrar</h2>
      <PokedexCard
        key={pokemon.species}
        game={game}
        pokemon={pokemon}
        onSkip={() => {
          setSkipped([...skipped, pokemon.species]);
        }}
      />
    </section>
  );
}
