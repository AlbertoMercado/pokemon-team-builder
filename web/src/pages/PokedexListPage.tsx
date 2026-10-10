/**
 * Pokédex (RF-20): the games recorded in the Hall of Fame, in the order of the journey, each
 * with the progress of its Pokédex. Each one leads to its Pokédex.
 */
import { Link } from "react-router";

import { usePokedexes } from "../api/queries/pokedex";
import ErrorMessage from "../components/ErrorMessage";
import GameCover from "../components/GameCover";
import PokedexProgress from "../components/PokedexProgress";

export default function PokedexListPage() {
  const pokedexes = usePokedexes();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Pokédex</h1>
      <p className="text-slate-700">
        Completa la Pokédex de los juegos que has superado y consigue su diploma. La aplicación te
        propone, uno a uno, el siguiente Pokémon que registrar y la forma más sencilla de obtenerlo.
      </p>
      {pokedexes.error !== null ? (
        <ErrorMessage error={pokedexes.error} />
      ) : pokedexes.data === undefined ? (
        <p className="text-slate-500">Cargando…</p>
      ) : pokedexes.data.length === 0 ? (
        <p>
          Todavía no has superado ningún juego. Cuando registres uno en el{" "}
          <Link to="/hall-of-fame" className="text-red-700 underline">
            Hall of Fame
          </Link>
          , aparecerá aquí su Pokédex.
        </p>
      ) : (
        <ul aria-label="Juegos superados" className="space-y-3">
          {pokedexes.data.map((pokedex) => (
            <li
              key={pokedex.game}
              className="flex flex-wrap items-center gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
            >
              <GameCover url={pokedex.cover_url} />
              <div className="grow space-y-1">
                <Link
                  to={`/pokedex/${pokedex.game}`}
                  className="text-lg font-semibold text-slate-900 hover:text-red-700"
                >
                  {pokedex.game_name}
                </Link>
                <PokedexProgress progress={pokedex.progress} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
