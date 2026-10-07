/**
 * Resultado (RF-08, RF-09, RF-10): generates the teams when it opens and with «Volver a
 * generar». It shows the state and its reason, each group of tied teams with its positions, the
 * breakdown by rule, the open slots with their suggestions, the discards by reason, the presence
 * rules and the confirmed data used. A `409` (data to confirm) leads to the review. The
 * selector (`TeamSelector`) chooses one of the teams and records it in the Hall of Fame.
 */
import { useState, type ReactNode } from "react";
import { Link, Navigate, useParams } from "react-router";

import { ApiError } from "../api/client";
import { useFavorites } from "../api/queries/favorites";
import { useGames } from "../api/queries/games";
import { useGeneration } from "../api/queries/generation";
import { usePokemonNames } from "../api/queries/pokemon";
import { useRuleNames } from "../api/queries/rules";
import type {
  HallOfFameEntry,
  ConfirmedFact,
  Discard,
  Generation,
  GeneratedPokemon,
  OpenSlots,
  Presence,
  Team,
  TeamGroup,
} from "../api/types";
import ErrorMessage from "../components/ErrorMessage";
import FavoriteButton from "../components/FavoriteButton";
import GameCover from "../components/GameCover";
import PokemonRow from "../components/PokemonRow";
import PokemonSprite from "../components/PokemonSprite";
import TeamSelector from "../components/TeamSelector";
import { TypeBadges } from "../components/TypeBadge";
import { formatDate, formatDateTime, formatDexNumber } from "../lib/format";
import {
  alternatives,
  DISCARD_REASONS,
  discardsByReason,
  discardSummary,
  INCOMPLETE_REASONS,
  PRESENCE_STATUS,
} from "../lib/generation";

/** Suggestions of a slot shown before «Ver más» (CA-50). */
const VISIBLE_SUGGESTIONS = 5;

const CARD = "space-y-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm";

export default function ResultPage() {
  const { game = "" } = useParams();
  const generation = useGeneration(game);
  const games = useGames();
  const found = games.data?.find((candidate) => candidate.game === game);
  const gameName = found?.name ?? game;
  // What the user did with the selector; it stays while the result is generated again.
  const [registered, setRegistered] = useState<HallOfFameEntry | null>(null);
  const [discarded, setDiscarded] = useState(false);

  if (generation.error instanceof ApiError && generation.error.status === 409) {
    return <Navigate to={`/juego/${game}/revision`} replace />;
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link to={`/juego/${game}/revision`} className="text-sm text-red-700 underline">
          Revisar los datos
        </Link>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-3">
            <GameCover url={found?.cover_url} />
            <h1 className="text-2xl font-bold">{`Resultado: ${gameName}`}</h1>
          </div>
          <button
            type="button"
            disabled={generation.isFetching}
            className="rounded border border-slate-300 bg-white px-3 py-1 text-sm font-medium hover:border-red-700 disabled:opacity-50"
            onClick={() => {
              void generation.refetch();
            }}
          >
            {generation.isFetching ? "Generando…" : "Volver a generar"}
          </button>
        </div>
      </div>
      {registered !== null && <Registered entry={registered} />}
      {discarded && (
        <p role="status" className="rounded border border-slate-200 bg-white px-3 py-2">
          Has descartado los equipos: no se ha registrado nada.{" "}
          <Link to="/" className="text-red-700 underline">
            Volver al inicio
          </Link>
        </p>
      )}
      {generation.error !== null ? (
        <ErrorMessage error={generation.error} />
      ) : generation.data === undefined ? (
        <p className="text-slate-500">Generando los equipos…</p>
      ) : (
        <Result
          game={game}
          generation={generation.data}
          selector={
            registered === null && !discarded && generation.data.groups.length > 0 ? (
              <TeamSelector
                game={game}
                groups={generation.data.groups}
                onRegistered={setRegistered}
                onDiscard={() => {
                  setDiscarded(true);
                }}
              />
            ) : null
          }
        />
      )}
    </div>
  );
}

function Registered({ entry }: { entry: HallOfFameEntry }) {
  return (
    <div role="status" className="rounded border border-green-300 bg-green-50 px-3 py-2">
      <p className="font-semibold text-green-900">
        {`Equipo registrado en el Hall of Fame: ${entry.game_name}, ${formatDate(entry.completed_on)}.`}
      </p>
      <p className="text-sm text-green-900">
        {`${entry.members.map((member) => member.name).join(", ")}. Desde ahora, sus líneas quedan excluidas de las próximas generaciones (RN-16), así que el resultado de abajo ya es otro.`}{" "}
        <Link to="/hall-of-fame" className="underline">
          Ver el Hall of Fame
        </Link>
      </p>
    </div>
  );
}

interface ResultProps {
  game: string;
  generation: Generation;
  selector: ReactNode;
}

function Result({ game, generation, selector }: ResultProps) {
  return (
    <>
      <Status generation={generation} />
      {generation.groups.map((group, index) => (
        <GroupCard
          key={group.teams.map((team) => team.members.join("+")).join("|")}
          group={group}
          title={
            generation.groups.length === 1 ? "Equipo recomendado" : `Opción ${String(index + 1)}`
          }
        />
      ))}
      {selector}
      {generation.discards.length > 0 && <Discards game={game} discards={generation.discards} />}
      {generation.presence.length > 0 && <PresenceRules presence={generation.presence} />}
      {generation.confirmed_facts.length > 0 && (
        <ConfirmedFacts game={game} facts={generation.confirmed_facts} />
      )}
      {generation.data_version !== null && (
        <p className="text-sm text-slate-500">
          {`Generado con los datos cargados el ${formatDateTime(generation.data_version.ingested_at)}.`}
        </p>
      )}
    </>
  );
}

function Status({ generation }: { generation: Generation }) {
  const teams = generation.groups.reduce((total, group) => total + group.teams.length, 0);
  const complete = generation.status === "complete";
  return (
    <section aria-label="Estado" className={CARD}>
      <p className="text-lg font-semibold">
        {complete ? "Equipo completo" : "Equipo incompleto"}
        <span className="ml-3 rounded bg-slate-100 px-2 py-0.5 text-base">{`Puntuación: ${String(generation.score)}`}</span>
      </p>
      {generation.incomplete_reason !== null && (
        <p>{INCOMPLETE_REASONS[generation.incomplete_reason]}</p>
      )}
      {teams > 1 && (
        <p className="text-slate-700">
          {`Hay ${String(teams)} equipos empatados con la misma puntuación. Los que solo se diferencian en Pokémon intercambiables, con los mismos tipos, se agrupan en una opción.`}
        </p>
      )}
      {teams === 0 && <p>No hay ningún equipo que cumpla las reglas.</p>}
    </section>
  );
}

/** What the teams of a group share; `null` if they differ and each one is shown apart. */
function shared<T>(teams: readonly Team[], pick: (team: Team) => T): T | null {
  const [first, ...rest] = teams.map(pick);
  const text = JSON.stringify(first);
  return first !== undefined && rest.every((other) => JSON.stringify(other) === text)
    ? first
    : null;
}

function GroupCard({ group, title }: { group: TeamGroup; title: string }) {
  const names = new Map(group.positions.flat().map((pokemon) => [pokemon.pokemon, pokemon.name]));
  const nameOf = (pokemon: string) => names.get(pokemon) ?? pokemon;
  const breakdown = shared(group.teams, (team) => team.breakdown);
  const openSlots = shared(group.teams, (team) => team.open_slots);
  const [firstTeam] = group.teams;

  return (
    <section aria-label={title} className={CARD}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <ol aria-label="Posiciones" className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
        {group.positions.map((position) => (
          <Position key={position.map((pokemon) => pokemon.pokemon).join("+")} options={position} />
        ))}
      </ol>
      {group.teams.length > 1 && (
        <p className="text-sm text-slate-600">
          {`Son ${String(group.teams.length)} equipos: elige un Pokémon de cada posición.`}
        </p>
      )}
      {breakdown !== null && firstTeam !== undefined ? (
        <>
          <Breakdown team={firstTeam} nameOf={nameOf} />
          {openSlots !== null && openSlots.length > 0 && <Slots slots={openSlots} />}
        </>
      ) : (
        group.teams.map((team) => (
          <div key={team.members.join("+")} className="space-y-3 border-t border-slate-200 pt-3">
            <h3 className="font-semibold">{team.members.map(nameOf).join(", ")}</h3>
            <Breakdown team={team} nameOf={nameOf} />
            {team.open_slots.length > 0 && <Slots slots={team.open_slots} />}
          </div>
        ))
      )}
    </section>
  );
}

function Position({ options }: { options: GeneratedPokemon[] }) {
  const [first] = options;
  return (
    <li className="space-y-1 rounded border border-slate-200 px-3 py-2">
      {options.some((pokemon) => pokemon.image_url) && (
        <div className="flex flex-wrap gap-1">
          {options.map((pokemon) => (
            <PokemonSprite key={pokemon.pokemon} url={pokemon.image_url} size="medium" />
          ))}
        </div>
      )}
      <p className="font-medium">{alternatives(options.map((pokemon) => pokemon.name))}</p>
      <p className="font-mono text-xs text-slate-500">
        {options.map((pokemon) => formatDexNumber(pokemon.dex_number)).join(" · ")}
      </p>
      {first !== undefined && <TypeBadges types={first.types} />}
    </li>
  );
}

function Breakdown({ team, nameOf }: { team: Team; nameOf: (pokemon: string) => string }) {
  return (
    <table className="w-full text-left text-sm">
      <caption className="text-left font-semibold">Puntuación por regla</caption>
      <thead className="text-slate-500">
        <tr>
          <th scope="col" className="py-1 pr-3 font-medium">
            Regla
          </th>
          <th scope="col" className="py-1 pr-3 text-right font-medium">
            Peso
          </th>
          <th scope="col" className="py-1 pr-3 text-right font-medium">
            Cumple
          </th>
          <th scope="col" className="py-1 pr-3 text-right font-medium">
            Aporta
          </th>
          <th scope="col" className="py-1 font-medium">
            En contra
          </th>
        </tr>
      </thead>
      <tbody>
        {team.breakdown.map((rule) => (
          <tr key={rule.rule_id} className="border-t border-slate-100">
            <th scope="row" className="py-1 pr-3 font-normal">
              <span className="font-mono text-xs text-slate-500">{rule.rule_id}</span> {rule.name}
            </th>
            <td className="py-1 pr-3 text-right">{rule.weight}</td>
            <td className="py-1 pr-3 text-right">{`${String(rule.score)} %`}</td>
            <td className="py-1 pr-3 text-right">{rule.contribution}</td>
            <td className="py-1">{rule.penalized.map(nameOf).join(", ")}</td>
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr className="border-t border-slate-300 font-semibold">
          <th scope="row" className="py-1 pr-3 text-left">
            Total
          </th>
          <td />
          <td />
          <td className="py-1 pr-3 text-right">{team.score}</td>
          <td />
        </tr>
      </tfoot>
    </table>
  );
}

function Slots({ slots }: { slots: OpenSlots[] }) {
  const ruleNames = useRuleNames();
  return (
    <div className="space-y-3">
      {slots.map((slot) => {
        const title =
          slot.rule_id === null
            ? slot.count === 1
              ? "1 hueco libre"
              : `${String(slot.count)} huecos libres`
            : `Hueco reservado por ${slot.rule_id}: ${ruleNames.data?.get(slot.rule_id) ?? ""}`;
        return (
          <section key={slot.rule_id ?? "free"} aria-label={title} className="space-y-2">
            <h3 className="font-semibold">{title}</h3>
            {slot.rule_id === null && slot.count > 1 && (
              <p className="text-sm text-slate-600">
                Cada sugerencia encaja con el equipo, pero no necesariamente con las demás.
              </p>
            )}
            <Suggestions slot={slot} />
          </section>
        );
      })}
    </div>
  );
}

function Suggestions({ slot }: { slot: OpenSlots }) {
  if (slot.suggestions.length === 0) {
    return <p className="text-sm">No hay ningún Pokémon que encaje.</p>;
  }
  const visible = slot.suggestions.slice(0, VISIBLE_SUGGESTIONS);
  const rest = slot.suggestions.slice(VISIBLE_SUGGESTIONS);
  return (
    <>
      <SuggestionList suggestions={visible} label="Sugerencias" />
      {rest.length > 0 && (
        <details>
          <summary className="cursor-pointer text-sm text-red-700">
            {`Ver ${String(rest.length)} sugerencias más`}
          </summary>
          <SuggestionList suggestions={rest} label="Más sugerencias" />
        </details>
      )}
    </>
  );
}

function SuggestionList({
  suggestions,
  label,
}: {
  suggestions: OpenSlots["suggestions"];
  label: string;
}) {
  return (
    <ul aria-label={label} className="divide-y divide-slate-100">
      {suggestions.map(({ pokemon, gain, verified }) => (
        <li key={pokemon.pokemon} className="py-1">
          <PokemonRow
            pokemon={pokemon.pokemon}
            name={pokemon.name}
            dexNumber={pokemon.dex_number}
            imageUrl={pokemon.image_url}
            types={pokemon.types}
            extra={
              <>
                <span className="text-sm text-slate-700">{`+${String(gain)}`}</span>
                {!verified && (
                  <span
                    title="Algún dato de este Pokémon está sin confirmar"
                    className="rounded bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900"
                  >
                    Sin verificar
                  </span>
                )}
              </>
            }
            action={
              <FavoriteButton pokemon={pokemon.pokemon} name={pokemon.name} favorite={false} />
            }
          />
        </li>
      ))}
    </ul>
  );
}

function Discards({ game, discards }: { game: string; discards: Discard[] }) {
  const favorites = useFavorites();
  return (
    <section aria-label="Favoritos descartados" className={CARD}>
      <h2 className="text-lg font-semibold">Favoritos descartados</h2>
      {favorites.data !== undefined && <p>{discardSummary(discards, favorites.data.total)}</p>}
      {discardsByReason(discards).map(([reason, found]) => (
        <div key={reason}>
          <h3 className="font-semibold">{DISCARD_REASONS[reason].title}</h3>
          <ul className="list-disc pl-5 text-sm">
            {found.map((discard) => (
              <li key={discard.pokemon}>
                {discard.detail}
                {discard.fact_key !== null && (
                  <>
                    {" "}
                    <Link to={`/juego/${game}/revision`} className="text-red-700 underline">
                      (dato que confirmaste)
                    </Link>
                  </>
                )}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function PresenceRules({ presence }: { presence: Presence[] }) {
  const ruleNames = useRuleNames();
  const names = usePokemonNames();
  return (
    <section aria-label="Reglas de presencia" className={CARD}>
      <h2 className="text-lg font-semibold">Reglas de presencia</h2>
      <ul className="space-y-2 text-sm">
        {presence.map((rule) => (
          <li key={rule.rule_id}>
            <p className="font-medium">
              <span className="font-mono text-xs text-slate-500">{rule.rule_id}</span>{" "}
              {ruleNames.data?.get(rule.rule_id) ?? ""}
            </p>
            <p>{`${PRESENCE_STATUS[rule.status]} (nivel ${String(rule.level)}): ${rule.detail}.`}</p>
            {rule.options.length > 0 && (
              <p className="text-slate-600">
                {`La cumplen: ${rule.options.map((pokemon) => names.data?.get(pokemon) ?? pokemon).join(", ")}.`}
              </p>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

function ConfirmedFacts({ game, facts }: { game: string; facts: ConfirmedFact[] }) {
  const names = usePokemonNames();
  const value = (fact: ConfirmedFact): ReactNode =>
    Array.isArray(fact.value)
      ? fact.value.map((pokemon) => names.data?.get(pokemon) ?? pokemon).join(", ")
      : fact.value
        ? "Sí"
        : "No";
  return (
    <section aria-label="Datos que confirmaste" className={CARD}>
      <h2 className="text-lg font-semibold">Datos que confirmaste</h2>
      <p className="text-sm text-slate-600">
        Se han usado tal cual para generar el equipo.{" "}
        <Link to={`/juego/${game}/revision`} className="text-red-700 underline">
          Cambiarlos
        </Link>
      </p>
      <ul className="text-sm">
        {facts.map((fact) => (
          <li key={fact.fact_key}>
            {fact.kind === "key_battle" ? `Equipo de ${fact.name}` : fact.name}: {value(fact)}
          </li>
        ))}
      </ul>
    </section>
  );
}
