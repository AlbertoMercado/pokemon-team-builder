/**
 * Inicio: the data the application works with, how many favourites there are, the last
 * completed game and the way to a new game (docs/02-ddt/plan-web.md, "Pantallas").
 */
import type { ReactNode } from "react";
import { Link } from "react-router";

import { isUnavailable } from "../api/client";
import { useFavorites } from "../api/queries/favorites";
import { useHallOfFame } from "../api/queries/hallOfFame";
import { useMeta } from "../api/queries/meta";
import type { FavoritesOut, HallOfFameEntry, Meta } from "../api/types";
import ErrorMessage from "../components/ErrorMessage";
import GameCover from "../components/GameCover";
import { formatDate, formatDateTime, shortCommit } from "../lib/format";

export default function HomePage() {
  const meta = useMeta();
  const favorites = useFavorites();
  const hallOfFame = useHallOfFame();

  // Without data or without API, the notice of the layout says what to do.
  const unavailable = [meta.error, favorites.error, hallOfFame.error].some(isUnavailable);

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-bold">Inicio</h1>
        <p className="mt-2 text-slate-700">
          Genera un equipo de 6 Pokémon para un juego a partir de tus favoritos y de tus reglas.
        </p>
      </section>
      {!unavailable && (
        <>
          <Card title="Nuevo juego">
            <p>Elige el juego, revisa sus datos y genera el equipo.</p>
            <Link
              to="/juego"
              className="mt-3 inline-block rounded bg-red-700 px-4 py-2 font-semibold text-white hover:bg-red-800"
            >
              Empezar un juego nuevo
            </Link>
          </Card>
          <div className="grid gap-6 md:grid-cols-3">
            <Card title="Favoritos">
              <Loaded query={favorites}>{(data) => <FavoritesSummary favorites={data} />}</Loaded>
            </Card>
            <Card title="Último juego completado">
              <Loaded query={hallOfFame}>{(data) => <LastGame entries={data} />}</Loaded>
            </Card>
            <Card title="Datos">
              <Loaded query={meta}>{(data) => <DataSummary meta={data} />}</Loaded>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-2 text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

interface Query<T> {
  data: T | undefined;
  error: Error | null;
}

function Loaded<T>({ query, children }: { query: Query<T>; children: (data: T) => ReactNode }) {
  if (query.error !== null) {
    return <ErrorMessage error={query.error} />;
  }
  if (query.data === undefined) {
    return <p className="text-slate-500">Cargando…</p>;
  }
  return children(query.data);
}

function FavoritesSummary({ favorites }: { favorites: FavoritesOut }) {
  if (favorites.total === 0) {
    return (
      <p>
        Todavía no tienes favoritos. Añádelos desde el{" "}
        <Link to="/pokemon" className="text-red-700 underline">
          catálogo
        </Link>
        .
      </p>
    );
  }
  return (
    <p>
      Tienes{" "}
      <Link to="/favoritos" className="font-semibold text-red-700 underline">
        {favorites.total} {favorites.total === 1 ? "favorito" : "favoritos"}
      </Link>
      .
    </p>
  );
}

function LastGame({ entries }: { entries: HallOfFameEntry[] }) {
  const last = entries.find((entry) => entry.last);
  if (last === undefined) {
    return <p>Todavía no has registrado ningún juego completado.</p>;
  }
  return (
    <div>
      <div className="flex items-center gap-3">
        <GameCover url={last.cover_url} size="small" />
        <p>
          <Link to="/hall-of-fame" className="font-semibold text-red-700 underline">
            {last.game_name}
          </Link>
          , el {formatDate(last.completed_on)}.
        </p>
      </div>
      <ul aria-label="Equipo" className="mt-2 flex flex-wrap gap-1">
        {last.members.map((member) => (
          <li key={member.position} className="rounded bg-slate-100 px-2 py-0.5 text-sm">
            {member.name}
          </li>
        ))}
      </ul>
    </div>
  );
}

function DataSummary({ meta }: { meta: Meta }) {
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
      <dt className="text-slate-500">Versión</dt>
      <dd>{meta.app_version}</dd>
      {meta.data === null ? (
        <>
          <dt className="text-slate-500">Carga</dt>
          <dd>Sin registro de la carga.</dd>
        </>
      ) : (
        <>
          <dt className="text-slate-500">Cargados</dt>
          <dd>{formatDateTime(meta.data.ingested_at)}</dd>
          <dt className="text-slate-500">Juegos</dt>
          <dd title={meta.data.games.join(", ")}>{meta.data.games.length}</dd>
          <dt className="text-slate-500">PokeAPI</dt>
          <dd>
            {meta.data.pokeapi_commit === null ? (
              "desconocido"
            ) : (
              <code title={meta.data.pokeapi_commit}>{shortCommit(meta.data.pokeapi_commit)}</code>
            )}
          </dd>
        </>
      )}
    </dl>
  );
}
