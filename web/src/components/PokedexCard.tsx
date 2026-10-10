/**
 * The card of a Pokémon in a Pokédex (RF-22, RF-23): number, name, image, types and how to
 * obtain it. It shows the way the user chose, marked «Elegida por ti», or else the simplest
 * one; the other ways open below, simplest first, to choose another (it is kept). If a way
 * starts from a Pokémon not registered (evolving or breeding it), it links to that one's card
 * (CA-76).
 *
 * Actions: register it, mark it as impossible, unmark it and, on the objective, skip it for
 * now (`onSkip`, not kept: CA-77). After a mark, the parent shows what comes next.
 */
import { useState } from "react";
import { Link } from "react-router";

import { useMarkPokemon, useUnmarkPokemon } from "../api/queries/pokedex";
import type { ObtentionMethod, PokedexMark, PokedexPokemon } from "../api/types";
import { formatDexNumber } from "../lib/format";
import { describeObtention } from "../lib/obtention";
import ErrorMessage from "./ErrorMessage";
import { PokemonArtwork } from "./PokemonSprite";
import { TypeBadges } from "./TypeBadge";

const BUTTON =
  "rounded border px-3 py-1 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50";
const PRIMARY = `${BUTTON} border-red-700 bg-red-700 text-white hover:bg-red-800`;
const SECONDARY = `${BUTTON} border-slate-300 bg-white hover:border-red-700`;

const STATUS = { registered: "Registrado", impossible: "Imposible de obtener" } as const;

interface Props {
  game: string;
  pokemon: PokedexPokemon;
  /** Skips it for now, on the objective. */
  onSkip?: () => void;
}

export default function PokedexCard({ game, pokemon, onSkip }: Props) {
  const mark = useMarkPokemon(game);
  const unmark = useUnmarkPokemon(game);
  const [others, setOthers] = useState(false);
  const shown =
    pokemon.methods.find((method) => method.chosen) ??
    pokemon.methods.find((method) => method.recommended);
  const busy = mark.isPending || unmark.isPending;
  const save = (change: PokedexMark) => {
    mark.mutate({ species: pokemon.species, mark: change });
  };

  return (
    <article
      aria-label={`Ficha de ${pokemon.name}`}
      className="space-y-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
    >
      <div className="flex flex-wrap items-center gap-3">
        <PokemonArtwork url={pokemon.artwork_url} spriteUrl={pokemon.image_url} />
        <div className="space-y-1">
          <div className="flex flex-wrap items-baseline gap-2">
            <span className="font-mono text-slate-500">{formatDexNumber(pokemon.number)}</span>
            <h2 className="text-xl font-bold">{pokemon.name}</h2>
            {pokemon.status !== null && (
              <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-800">
                {STATUS[pokemon.status]}
              </span>
            )}
          </div>
          <TypeBadges types={pokemon.types} />
        </div>
      </div>

      {shown === undefined ? (
        <p className="text-slate-700">
          {pokemon.automatically_impossible
            ? "Solo se obtiene en spin-offs, que no cuentan: es imposible de obtener."
            : "No se conoce ninguna forma de obtenerlo en este juego. Si no puedes conseguirlo, márcalo como imposible."}
        </p>
      ) : (
        <div className="space-y-1">
          <p className="text-sm font-semibold text-slate-600">
            {shown.chosen ? "Elegida por ti" : "La forma más sencilla"}
          </p>
          <Method game={game} species={pokemon.species} method={shown} />
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {pokemon.status !== "registered" && (
          <button
            type="button"
            className={PRIMARY}
            disabled={busy}
            onClick={() => {
              save({ status: "registered" });
            }}
          >
            Registrado
          </button>
        )}
        {pokemon.status !== "impossible" && (
          <button
            type="button"
            className={SECONDARY}
            disabled={busy}
            onClick={() => {
              save({ status: "impossible" });
            }}
          >
            Imposible de obtener
          </button>
        )}
        {pokemon.status !== null && (
          <button
            type="button"
            className={SECONDARY}
            disabled={busy}
            onClick={() => {
              unmark.mutate(pokemon.species);
            }}
          >
            Desmarcar
          </button>
        )}
        {pokemon.methods.length > 1 && (
          <button
            type="button"
            className={SECONDARY}
            aria-expanded={others}
            onClick={() => {
              setOthers(!others);
            }}
          >
            {others ? "Ocultar otras formas" : "Otras formas de obtenerlo"}
          </button>
        )}
        {onSkip !== undefined && (
          <button type="button" className={SECONDARY} disabled={busy} onClick={onSkip}>
            Saltar de momento
          </button>
        )}
      </div>

      {others && (
        <ol aria-label="Formas de obtenerlo" className="space-y-2">
          {pokemon.methods.map((method) => (
            <li
              key={method.key}
              className="flex flex-wrap items-center gap-2 rounded border border-slate-200 px-3 py-2"
            >
              <Method game={game} species={pokemon.species} method={method} />
              {method.recommended && <Tag>Recomendada</Tag>}
              {method.chosen && <Tag>Elegida por ti</Tag>}
              {method.chosen ? (
                <button
                  type="button"
                  className={SECONDARY}
                  disabled={busy}
                  onClick={() => {
                    save({ chosen_method: null });
                  }}
                >
                  Volver a la recomendada
                </button>
              ) : (
                method !== shown && (
                  <button
                    type="button"
                    className={SECONDARY}
                    disabled={busy}
                    onClick={() => {
                      save({ chosen_method: method.key });
                    }}
                  >
                    Elegir esta
                  </button>
                )
              )}
            </li>
          ))}
        </ol>
      )}

      {mark.error !== null && <ErrorMessage error={mark.error} />}
      {unmark.error !== null && <ErrorMessage error={unmark.error} />}
    </article>
  );
}

function Tag({ children }: { children: string }) {
  return (
    <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-900">
      {children}
    </span>
  );
}

/** The text of a way and, if it starts from a Pokémon not registered, the link to it. */
function Method({
  game,
  species,
  method,
}: {
  game: string;
  species: string;
  method: ObtentionMethod;
}) {
  const from = method.pokemon;
  return (
    <span className="grow">
      {describeObtention(method, species)}
      {from !== null && !method.pokemon_registered && (
        <>
          {" · "}
          <Link to={`/pokedex/${game}/pokemon/${from}`} className="text-red-700 underline">
            {`Cómo obtener ${method.pokemon_name ?? from}`}
          </Link>
        </>
      )}
    </span>
  );
}
