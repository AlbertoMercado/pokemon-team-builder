/**
 * Selector of the team (RF-12, CA-53): in the result, the user chooses one of the teams (an
 * option, one Pokémon of each position and one suggestion for each open slot), and the API
 * checks it against the rules before it is recorded in the Hall of Fame. A team with problems
 * cannot be recorded from here; the user can also discard every team, and nothing is recorded.
 *
 * The web only validates the shape of the choice (a suggestion for each slot, none repeated);
 * the rules are checked by the API (POST /api/games/{game}/team-checks).
 */
import { useState } from "react";

import { useCheckTeam } from "../api/queries/generation";
import { useAddHallOfFameEntry } from "../api/queries/hallOfFame";
import type { HallOfFameEntry, TeamCheck, TeamGroup } from "../api/types";
import { todayIso } from "../lib/format";
import { alternatives } from "../lib/generation";
import ErrorMessage from "./ErrorMessage";
import PokemonSprite from "./PokemonSprite";

const FIELD = "rounded border border-slate-300 bg-white px-2 py-1";
const BUTTON = "rounded px-4 py-2 font-semibold disabled:cursor-not-allowed disabled:opacity-50";

interface Props {
  game: string;
  groups: TeamGroup[];
  onRegistered: (entry: HallOfFameEntry) => void;
  onDiscard: () => void;
}

export default function TeamSelector({ game, groups, onRegistered, onDiscard }: Props) {
  const [groupIndex, setGroupIndex] = useState(0);
  const [positionPicks, setPositionPicks] = useState<Record<number, string>>({});
  const [slotPicks, setSlotPicks] = useState<Record<string, string>>({});
  const [date, setDate] = useState(todayIso);
  const [notes, setNotes] = useState("");
  const check = useCheckTeam(game);
  const add = useAddHallOfFameEntry();

  const group = groups[groupIndex] ?? groups[0];
  if (group === undefined) {
    return null;
  }

  const chosen = group.positions.map(
    (position, index) => positionPicks[index] ?? position[0]?.pokemon ?? "",
  );
  const team =
    group.teams.find((candidate) => sameMembers(candidate.members, chosen)) ?? group.teams[0];
  const holes = (team?.open_slots ?? []).flatMap((slot, slotIndex) =>
    Array.from({ length: slot.count }, (_, hole) => ({
      key: `${String(slotIndex)}-${String(hole)}`,
      slot,
      label:
        slot.rule_id === null
          ? `Hueco libre ${String(hole + 1)}`
          : `Hueco reservado por ${slot.rule_id}`,
    })),
  );
  const names = new Map<string, string>([
    ...group.positions.flat().map((p): [string, string] => [p.pokemon, p.name]),
    ...holes.flatMap(({ slot }) =>
      slot.suggestions.map((s): [string, string] => [s.pokemon.pokemon, s.pokemon.name]),
    ),
  ]);
  const picked = holes.map(({ key }) => slotPicks[key]).filter((slug) => slug !== undefined);
  const members = [...chosen, ...picked];

  const missing = holes.some(({ key, slot }) => slot.suggestions.length > 0 && !slotPicks[key]);
  const repeated = new Set(members).size !== members.length;
  const shapeError = missing
    ? "Elige una sugerencia para cada hueco."
    : repeated
      ? "No elijas dos veces el mismo Pokémon."
      : null;

  const changed = () => {
    check.reset();
    add.reset();
  };

  const submit = async () => {
    const result = await check.mutateAsync(members);
    if (!result.valid) return;
    onRegistered(
      await add.mutateAsync({
        game,
        completed_on: date,
        notes: notes.trim() === "" ? null : notes.trim(),
        members,
      }),
    );
  };

  return (
    <section
      aria-label="Elegir el equipo"
      className="space-y-4 rounded-lg border border-red-200 bg-white p-4 shadow-sm"
    >
      <h2 className="text-lg font-semibold">Elegir el equipo</h2>
      <p className="text-sm text-slate-700">
        Elige el equipo con el que vas a jugar. Se comprueba con tus reglas y se registra en tu{" "}
        <i>Hall of Fame</i>: desde ese momento, la próxima generación excluye sus líneas.
      </p>

      {groups.length > 1 && (
        <fieldset className="space-y-1">
          <legend className="font-medium">Opción</legend>
          {groups.map((candidate, index) => (
            <label key={String(index)} className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="group"
                checked={index === groupIndex}
                onChange={() => {
                  setGroupIndex(index);
                  setPositionPicks({});
                  setSlotPicks({});
                  changed();
                }}
              />
              {`Opción ${String(index + 1)}: ${candidate.positions
                .map((position) => alternatives(position.map((p) => p.name)))
                .join(", ")}`}
            </label>
          ))}
        </fieldset>
      )}

      {group.positions.map(
        (position, index) =>
          position.length > 1 && (
            <fieldset key={String(index)} className="space-y-1">
              <legend className="font-medium">{`Posición ${String(index + 1)}`}</legend>
              {position.map((pokemon) => (
                <label key={pokemon.pokemon} className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name={`position-${String(index)}`}
                    checked={chosen[index] === pokemon.pokemon}
                    onChange={() => {
                      setPositionPicks({ ...positionPicks, [index]: pokemon.pokemon });
                      changed();
                    }}
                  />
                  <PokemonSprite url={pokemon.image_url} />
                  {pokemon.name}
                </label>
              ))}
            </fieldset>
          ),
      )}

      {holes.map(({ key, slot, label }) => (
        <label key={key} className="flex flex-col text-sm">
          {label}
          <select
            className={FIELD}
            value={slotPicks[key] ?? ""}
            disabled={slot.suggestions.length === 0}
            onChange={(event) => {
              // An empty choice removes the pick of the slot.
              const next = { ...slotPicks, [key]: event.target.value };
              setSlotPicks(Object.fromEntries(Object.entries(next).filter(([, v]) => v !== "")));
              changed();
            }}
          >
            <option value="">
              {slot.suggestions.length === 0 ? "No hay sugerencias" : "Elige una sugerencia"}
            </option>
            {slot.suggestions.map(({ pokemon, verified }) => (
              <option key={pokemon.pokemon} value={pokemon.pokemon}>
                {verified ? pokemon.name : `${pokemon.name} (sin verificar)`}
              </option>
            ))}
          </select>
        </label>
      ))}

      <p className="text-sm">
        <span className="font-medium">Equipo elegido: </span>
        {members.map((slug) => names.get(slug) ?? slug).join(", ")}
      </p>

      <div className="flex flex-wrap gap-4">
        <label className="flex flex-col text-sm">
          Fecha
          <input
            type="date"
            required
            className={FIELD}
            value={date}
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

      {shapeError !== null && <p className="text-sm text-slate-700">{shapeError}</p>}
      {check.data !== undefined && <CheckResult check={check.data} names={names} />}
      {check.error !== null && <ErrorMessage error={check.error} />}
      {add.error !== null && <ErrorMessage error={add.error} />}

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className={`${BUTTON} bg-red-700 text-white hover:bg-red-800`}
          disabled={shapeError !== null || date === "" || check.isPending || add.isPending}
          onClick={() => {
            submit().catch(() => {
              // The error is in the state of the mutation and is shown above.
            });
          }}
        >
          Comprobar y registrar
        </button>
        <button
          type="button"
          className={`${BUTTON} border border-slate-300 bg-white hover:border-red-700`}
          onClick={onDiscard}
        >
          Descartar los equipos
        </button>
      </div>
    </section>
  );
}

function sameMembers(a: readonly string[], b: readonly string[]): boolean {
  return a.length === b.length && a.every((slug) => b.includes(slug));
}

function CheckResult({ check, names }: { check: TeamCheck; names: Map<string, string> }) {
  const unverified = check.unverified.map((slug) => names.get(slug) ?? slug);
  return (
    <>
      {!check.valid && (
        <div
          role="alert"
          className="rounded border border-red-200 bg-red-50 px-3 py-2 text-red-900"
        >
          <p className="font-semibold">El equipo no cumple tus reglas, así que no se registra:</p>
          <ul className="list-disc pl-5 text-sm">
            {check.problems.map((problem) => (
              <li key={`${problem.rule_id}-${problem.members.join("+")}`}>
                <span className="font-mono text-xs">{problem.rule_id}</span> {problem.detail}
              </li>
            ))}
          </ul>
        </div>
      )}
      {unverified.length > 0 && (
        <p className="text-sm text-amber-900">
          {`Con datos sin verificar: ${unverified.join(", ")}.`}
        </p>
      )}
    </>
  );
}
