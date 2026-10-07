/**
 * Hall of Fame (RF-12, RF-13, RN-16): the journey in order, with the last completed game
 * marked and a filter by game (`?game=`). An entry is recorded by hand (also for a game that is
 * not a target game), corrected or removed after a confirmation. Each game is recorded once
 * (CA-68): the form leaves out the games already recorded. Every change alters the exclusions
 * of RN-16 from the next generation on.
 */
import { useState } from "react";
import { useSearchParams } from "react-router";

import { useGames } from "../api/queries/games";
import {
  useAddHallOfFameEntry,
  useHallOfFame,
  useRemoveHallOfFameEntry,
  useUpdateHallOfFameEntry,
} from "../api/queries/hallOfFame";
import type { Game, HallOfFameEntry, HallOfFameEntryIn } from "../api/types";
import ErrorMessage from "../components/ErrorMessage";
import GameCover from "../components/GameCover";
import PokemonSprite from "../components/PokemonSprite";
import TeamEditor, { TEAM_SIZE } from "../components/TeamEditor";
import { TypeBadges } from "../components/TypeBadge";
import { formatDate, todayIso } from "../lib/format";

const FIELD = "rounded border border-slate-300 bg-white px-2 py-1";
const BUTTON =
  "rounded border px-3 py-1 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50";
const PRIMARY = `${BUTTON} border-red-700 bg-red-700 text-white hover:bg-red-800`;
const SECONDARY = `${BUTTON} border-slate-300 bg-white hover:border-red-700`;

export default function HallOfFamePage() {
  const [params, setParams] = useSearchParams();
  const game = params.get("game") ?? undefined;
  const entries = useHallOfFame(game);
  const games = useGames({ all: true });
  const add = useAddHallOfFameEntry();
  const [adding, setAdding] = useState(false);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Hall of Fame</h1>
      <p className="text-slate-700">
        Tu recorrido: los juegos que has completado y su equipo, en orden de fecha. Al generar un
        equipo se excluyen las líneas evolutivas que ya usaste en el último juego completado y en
        los de la misma generación que el que vas a jugar.
      </p>

      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col text-sm">
          Juego
          <select
            className={FIELD}
            value={game ?? ""}
            onChange={(event) => {
              setParams(event.target.value ? { game: event.target.value } : {}, { replace: true });
            }}
          >
            <option value="">Todos</option>
            {games.data?.map((option) => (
              <option key={option.game} value={option.game}>
                {option.name}
              </option>
            ))}
          </select>
        </label>
        {!adding && (
          <button
            type="button"
            className={PRIMARY}
            onClick={() => {
              setAdding(true);
            }}
          >
            Registrar un equipo
          </button>
        )}
      </div>

      {adding && (
        <EntryForm
          title="Registrar un equipo"
          games={games.data ?? []}
          initial={{
            // The filtered game, unless it is already recorded (CA-68).
            game: games.data?.some((option) => option.game === game && !option.completed)
              ? (game ?? "")
              : "",
            completed_on: todayIso(),
            notes: null,
            members: [],
          }}
          saving={add.isPending}
          error={add.error}
          onSave={(entry) => {
            add.mutate(entry, {
              onSuccess: () => {
                setAdding(false);
              },
            });
          }}
          onCancel={() => {
            setAdding(false);
            add.reset();
          }}
        />
      )}

      {entries.error !== null ? (
        <ErrorMessage error={entries.error} />
      ) : entries.data === undefined ? (
        <p className="text-slate-500">Cargando…</p>
      ) : entries.data.length === 0 ? (
        <p>
          {game === undefined
            ? "Todavía no has registrado ningún juego completado."
            : "No hay ningún registro de este juego."}
        </p>
      ) : (
        <ol aria-label="Recorrido" className="space-y-3">
          {entries.data.map((entry) => (
            <Entry key={entry.id} entry={entry} games={games.data ?? []} />
          ))}
        </ol>
      )}
    </div>
  );
}

function Entry({ entry, games }: { entry: HallOfFameEntry; games: Game[] }) {
  const update = useUpdateHallOfFameEntry();
  const remove = useRemoveHallOfFameEntry();
  const [editing, setEditing] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const title = `${entry.game_name}, ${formatDate(entry.completed_on)}`;

  if (editing) {
    return (
      <li aria-label={title}>
        <EntryForm
          title={`Corregir: ${title}`}
          games={games}
          initial={{
            game: entry.game,
            completed_on: entry.completed_on,
            notes: entry.notes,
            members: entry.members.map((member) => member.pokemon),
          }}
          saving={update.isPending}
          error={update.error}
          onSave={(change) => {
            update.mutate(
              { id: entry.id, change },
              {
                onSuccess: () => {
                  setEditing(false);
                },
              },
            );
          }}
          onCancel={() => {
            setEditing(false);
            update.reset();
          }}
        />
      </li>
    );
  }

  return (
    <li
      aria-label={title}
      className={`space-y-2 rounded-lg border bg-white p-4 shadow-sm ${
        entry.last ? "border-red-300" : "border-slate-200"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-mono text-sm text-slate-500">{`${String(entry.order)}.`}</span>
        <GameCover url={entry.cover_url} size="small" />
        <h2 className="text-lg font-semibold">{entry.game_name}</h2>
        <span className="text-slate-600">{formatDate(entry.completed_on)}</span>
        {entry.last && (
          <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-900">
            Último juego completado
          </span>
        )}
      </div>
      {entry.notes !== null && <p className="text-sm text-slate-700">{entry.notes}</p>}
      <ol aria-label="Equipo" className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
        {entry.members.map((member) => (
          <li
            key={member.position}
            className="flex flex-wrap items-center gap-2 rounded border border-slate-200 px-2 py-1"
          >
            <PokemonSprite url={member.image_url} />
            <span className="font-medium">{member.name}</span>
            <TypeBadges types={member.types} />
          </li>
        ))}
      </ol>
      {confirming ? (
        <div role="alertdialog" aria-label="Confirmar la eliminación" className="space-y-2">
          <p className="text-sm">
            ¿Eliminar este registro? Sus líneas dejarán de excluirse en las próximas generaciones.
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              className={PRIMARY}
              disabled={remove.isPending}
              onClick={() => {
                remove.mutate(entry.id);
              }}
            >
              Sí, eliminar
            </button>
            <button
              type="button"
              className={SECONDARY}
              onClick={() => {
                setConfirming(false);
                remove.reset();
              }}
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <div className="flex gap-2">
          <button
            type="button"
            className={SECONDARY}
            onClick={() => {
              setEditing(true);
            }}
          >
            Corregir
          </button>
          <button
            type="button"
            className={SECONDARY}
            onClick={() => {
              setConfirming(true);
            }}
          >
            Eliminar
          </button>
        </div>
      )}
      {remove.error !== null && <ErrorMessage error={remove.error} />}
    </li>
  );
}

interface EntryFormProps {
  title: string;
  games: Game[];
  initial: HallOfFameEntryIn;
  saving: boolean;
  error: Error | null;
  onSave: (entry: HallOfFameEntryIn) => void;
  onCancel: () => void;
}

/** The fields of an entry. The web only checks the shape (1 to 6 Pokémon); the rest, the API. */
function EntryForm({ title, games, initial, saving, error, onSave, onCancel }: EntryFormProps) {
  const [game, setGame] = useState(initial.game);
  const [date, setDate] = useState(initial.completed_on);
  // Each game is recorded once (CA-68): the completed ones are left out, except this entry's.
  const choices = games.filter((option) => !option.completed || option.game === initial.game);
  const [notes, setNotes] = useState(initial.notes ?? "");
  const [members, setMembers] = useState<string[]>([...initial.members]);
  const missing =
    game === ""
      ? "Elige el juego."
      : date === ""
        ? "Indica la fecha."
        : members.length === 0
          ? `Añade de 1 a ${String(TEAM_SIZE)} Pokémon.`
          : null;

  return (
    <form
      aria-label={title}
      className="space-y-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        onSave({
          game,
          completed_on: date,
          notes: notes.trim() === "" ? null : notes.trim(),
          members,
        });
      }}
    >
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="flex flex-wrap gap-4">
        <label className="flex flex-col text-sm">
          Juego
          <select
            className={FIELD}
            value={game}
            required
            onChange={(event) => {
              setGame(event.target.value);
            }}
          >
            <option value="">Elige un juego</option>
            {choices.map((option) => (
              <option key={option.game} value={option.game}>
                {option.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-sm">
          Fecha
          <input
            type="date"
            className={FIELD}
            value={date}
            required
            onChange={(event) => {
              setDate(event.target.value);
            }}
          />
        </label>
        <label className="flex grow flex-col text-sm">
          Notas (opcional)
          <input
            type="text"
            className={FIELD}
            value={notes}
            onChange={(event) => {
              setNotes(event.target.value);
            }}
          />
        </label>
      </div>
      <TeamEditor team={members} onChange={setMembers} label="Equipo del registro" />
      {missing !== null && <p className="text-sm text-slate-700">{missing}</p>}
      {error !== null && <ErrorMessage error={error} />}
      <div className="flex gap-2">
        <button type="submit" className={PRIMARY} disabled={saving || missing !== null}>
          Guardar
        </button>
        <button type="button" className={SECONDARY} onClick={onCancel}>
          Cancelar
        </button>
      </div>
    </form>
  );
}
