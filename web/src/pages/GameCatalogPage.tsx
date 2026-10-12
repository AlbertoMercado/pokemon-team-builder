/**
 * Juegos (RF-25): the game catalogue, by generation, where the user chooses their target games.
 *
 * Choosing a game whose playability is not known first asks whether the user can play it on a
 * current Nintendo system (CA-92). If the API refuses the selection (`409`), the card says why:
 * it cannot receive a bred Pokémon, it lacks data or it is not playable (RF-05). A selected
 * game that no longer meets a condition stays selected, and the card says why it is not offered
 * (CA-93).
 */
import { useState } from "react";
import { Link } from "react-router";

import { selectionRefusal } from "../api/client";
import { useChooseGame, useGameCatalog } from "../api/queries/gameCatalog";
import type { CatalogGame, Reason } from "../api/types";
import ErrorMessage from "../components/ErrorMessage";
import GameCover from "../components/GameCover";

const PLATFORMS: Record<string, string> = {
  game_boy: "Game Boy",
  game_boy_color: "Game Boy Color",
  game_boy_advance: "Game Boy Advance",
  ds: "Nintendo DS",
  "3ds": "Nintendo 3DS",
  switch: "Nintendo Switch",
};
const BUTTON = "rounded border px-3 py-1 text-sm font-medium disabled:opacity-50";
const PRIMARY = `${BUTTON} border-red-700 bg-red-700 text-white hover:bg-red-800`;
const SECONDARY = `${BUTTON} border-slate-300 bg-white text-slate-800 hover:border-red-700`;

export default function GameCatalogPage() {
  const catalog = useGameCatalog();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Juegos</h1>
      <p className="text-slate-700">
        Elige los juegos que quieres completar: serán tus juegos objetivo en{" "}
        <Link to="/juego" className="text-red-700 underline">
          Nuevo juego
        </Link>
        . Solo se pueden elegir los que pueden recibir un Pokémon criado en otro juego, tienen todos
        los datos que necesitan las reglas y puedes jugar en un sistema actual de Nintendo.
      </p>
      {catalog.error !== null ? (
        <ErrorMessage error={catalog.error} />
      ) : catalog.data === undefined ? (
        <p className="text-slate-500">Cargando…</p>
      ) : (
        byGeneration(catalog.data).map(([generation, games]) => (
          <section key={generation} aria-labelledby={`generation-${String(generation)}`}>
            <h2 id={`generation-${String(generation)}`} className="mb-2 text-lg font-semibold">
              {`${String(generation)}.ª generación`}
            </h2>
            <ul
              aria-label={`Juegos de la ${String(generation)}.ª generación`}
              className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
            >
              {games.map((game) => (
                <GameCard key={game.game} game={game} />
              ))}
            </ul>
          </section>
        ))
      )}
    </div>
  );
}

function byGeneration(games: CatalogGame[]): [number, CatalogGame[]][] {
  const groups = new Map<number, CatalogGame[]>();
  for (const game of games) {
    groups.set(game.generation, [...(groups.get(game.generation) ?? []), game]);
  }
  return [...groups.entries()];
}

function GameCard({ game }: { game: CatalogGame }) {
  const choose = useChooseGame();
  const [asking, setAsking] = useState(false);
  const refusal = selectionRefusal(choose.error);
  const select = (playable?: boolean) => {
    setAsking(false);
    choose.mutate({ game: game.game, selected: true, playable });
  };
  const unknown = !game.known_playable && game.playable === null;
  return (
    <li
      aria-label={game.name}
      className={`h-full space-y-2 rounded-lg border bg-white p-3 shadow-sm ${
        game.target ? "border-emerald-400" : "border-slate-200"
      }`}
    >
      <div className="flex items-center gap-3">
        <GameCover url={game.cover_url} size="small" />
        <div className="min-w-0">
          <p className="truncate font-semibold">{game.name}</p>
          <p className="text-sm text-slate-600">{PLATFORMS[game.platform] ?? game.platform}</p>
        </div>
      </div>
      <Status game={game} />
      {!game.known_playable && game.playable !== null && (
        <p className="text-sm text-slate-700">
          {game.playable
            ? "Has indicado que puedes jugarlo en un sistema actual."
            : "Has indicado que no puedes jugarlo en un sistema actual."}{" "}
          <button
            type="button"
            className="text-red-700 underline"
            disabled={choose.isPending}
            onClick={() => {
              choose.mutate({ game: game.game, playable: !game.playable });
            }}
          >
            Cambiar
          </button>
        </p>
      )}
      {asking ? (
        <div role="group" aria-label={`¿Puedes jugar a ${game.name} en un sistema actual?`}>
          <p className="text-sm font-medium">
            ¿Puedes jugarlo en un sistema actual de Nintendo (Nintendo Switch 2)?
          </p>
          <div className="mt-1 flex gap-2">
            <button
              type="button"
              className={PRIMARY}
              onClick={() => {
                select(true);
              }}
            >
              Sí
            </button>
            <button
              type="button"
              className={SECONDARY}
              onClick={() => {
                select(false);
              }}
            >
              No
            </button>
            <button
              type="button"
              className={SECONDARY}
              onClick={() => {
                setAsking(false);
              }}
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : game.selected ? (
        <button
          type="button"
          className={SECONDARY}
          disabled={choose.isPending}
          onClick={() => {
            choose.mutate({ game: game.game, selected: false });
          }}
        >
          Quitar
        </button>
      ) : (
        <button
          type="button"
          className={PRIMARY}
          disabled={choose.isPending}
          onClick={() => {
            if (unknown) {
              setAsking(true);
            } else {
              select();
            }
          }}
        >
          Elegir como juego objetivo
        </button>
      )}
      {refusal !== undefined ? (
        <div role="alert" className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm">
          <p className="font-medium text-red-800">No se puede elegir como juego objetivo:</p>
          <Reasons obstacles={refusal.obstacles} missing={refusal.missing} />
        </div>
      ) : (
        choose.error !== null && <ErrorMessage error={choose.error} />
      )}
    </li>
  );
}

/** Whether the game is a target, completed, or selected but not offered and why (CA-93). */
function Status({ game }: { game: CatalogGame }) {
  if (game.target) {
    return <p className="text-sm font-medium text-emerald-700">Juego objetivo</p>;
  }
  if (game.selected && game.completed) {
    return (
      <p className="text-sm text-slate-600">
        Elegido, pero ya está en tu Hall of Fame: no se ofrece mientras lo esté.
      </p>
    );
  }
  if (game.selected) {
    return (
      <div className="text-sm text-amber-800">
        <p>Elegido, pero ahora no se puede ofrecer:</p>
        <Reasons obstacles={game.obstacles} missing={game.missing} />
      </div>
    );
  }
  return null;
}

/** The obstacles in order; for the missing data, what is missing instead of the generic one. */
function Reasons({ obstacles, missing }: { obstacles: Reason[]; missing: Reason[] }) {
  const lines = obstacles.flatMap((obstacle) =>
    obstacle.code === "missing_data" && missing.length > 0 ? missing : [obstacle],
  );
  return (
    <ul className="list-disc pl-5">
      {lines.map((reason) => (
        <li key={reason.code}>{reason.text}</li>
      ))}
    </ul>
  );
}
