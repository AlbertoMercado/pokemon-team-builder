/** Nuevo juego (RF-05): the target games to choose one; next comes the review of its data. */
import { Link } from "react-router";

import { useGames } from "../api/queries/games";
import ErrorMessage from "../components/ErrorMessage";
import GameCover from "../components/GameCover";

export default function GamesPage() {
  const games = useGames();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Nuevo juego</h1>
      <p className="text-slate-700">
        Elige el juego que vas a completar. Después revisarás sus datos y se generará el equipo con
        tus favoritos y tus reglas.
      </p>
      {games.error !== null ? (
        <ErrorMessage error={games.error} />
      ) : games.data === undefined ? (
        <p className="text-slate-500">Cargando…</p>
      ) : games.data.length === 0 ? (
        <p>No hay ningún juego objetivo en los datos cargados.</p>
      ) : (
        <ul aria-label="Juegos" className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
          {games.data.map((game) => (
            <li key={game.game}>
              <Link
                to={`/juego/${game.game}/revision`}
                className="flex items-center gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm hover:border-red-700"
              >
                <GameCover url={game.cover_url} size="large" />
                <span>
                  <span className="block text-lg font-semibold">{game.name}</span>
                  <span className="text-sm text-slate-600">{`${String(game.generation)}.ª generación`}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
