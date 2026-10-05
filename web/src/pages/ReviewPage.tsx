/**
 * Revisión de datos (RF-15, RN-18): the inferred or pending data that take part in the
 * generation, with their proposal. They are accepted all at once or confirmed or corrected one
 * by one; a key battle's team is corrected with the Pokémon picker. With everything confirmed,
 * the way to the result opens.
 */
import { useState } from "react";
import { Link, useParams } from "react-router";

import { useAcceptProposals, useConfirmFact, useGames, useReview } from "../api/queries/games";
import { usePokemonNames } from "../api/queries/pokemon";
import type { Review, ReviewFact } from "../api/types";
import ErrorMessage from "../components/ErrorMessage";
import TeamEditor from "../components/TeamEditor";

const GROUPS = [
  { title: "Mecánicas del juego", kinds: ["mechanic"] },
  { title: "Combates clave", kinds: ["key_battle"] },
  { title: "Favoritos", kinds: ["exists", "arrival"] },
] as const;

const BUTTON =
  "rounded border px-3 py-1 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50";
const PRIMARY = `${BUTTON} border-red-700 bg-red-700 text-white hover:bg-red-800`;
const SECONDARY = `${BUTTON} border-slate-300 bg-white hover:border-red-700`;

export default function ReviewPage() {
  const { game = "" } = useParams();
  const review = useReview(game);
  const games = useGames();
  const gameName = games.data?.find((candidate) => candidate.game === game)?.name ?? game;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Link to="/juego" className="text-sm text-red-700 underline">
          Elegir otro juego
        </Link>
        <h1 className="text-2xl font-bold">{`Revisión de datos: ${gameName}`}</h1>
        <p className="text-slate-700">
          Estos datos no se han podido cargar con certeza y se usan para generar tu equipo.
          Confírmalos con la propuesta o corrígelos.
        </p>
        <p
          role="note"
          className="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-950"
        >
          Los datos que confirmas se usan tal cual: si confirmas uno erróneo, el equipo propuesto
          puede ser inexacto. No es un error del algoritmo, sino de los datos de entrada.
        </p>
      </div>
      {review.error !== null ? (
        <ErrorMessage error={review.error} />
      ) : review.data === undefined ? (
        <p className="text-slate-500">Cargando…</p>
      ) : (
        <ReviewContent game={game} gameName={gameName} review={review.data} />
      )}
    </div>
  );
}

function ReviewContent({
  game,
  gameName,
  review,
}: {
  game: string;
  gameName: string;
  review: Review;
}) {
  return (
    <>
      <Summary game={game} review={review} />
      {GROUPS.map(({ title, kinds }) => {
        const facts = review.facts.filter((fact) =>
          (kinds as readonly string[]).includes(fact.kind),
        );
        return (
          facts.length > 0 && (
            <section key={title} aria-labelledby={`group-${title}`} className="space-y-3">
              <h2 id={`group-${title}`} className="text-lg font-semibold">
                {title}
              </h2>
              <ul className="space-y-3">
                {facts.map((fact) => (
                  <FactCard key={fact.fact_key} game={game} gameName={gameName} fact={fact} />
                ))}
              </ul>
            </section>
          )
        );
      })}
    </>
  );
}

function Summary({ game, review }: { game: string; review: Review }) {
  const accept = useAcceptProposals(game);
  const acceptable = review.facts.some(
    (fact) => fact.status === "pending" && fact.origin === "inferred" && fact.proposal !== null,
  );
  return (
    <section
      aria-label="Estado de la revisión"
      className="space-y-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
    >
      <p aria-live="polite" className="font-semibold">
        {review.facts.length === 0
          ? "No hay datos que revisar."
          : review.pending === 0
            ? "Todos los datos están confirmados."
            : review.pending === 1
              ? "Falta 1 dato por confirmar."
              : `Faltan ${String(review.pending)} datos por confirmar.`}
      </p>
      <div className="flex flex-wrap items-center gap-3">
        {acceptable && (
          <button
            type="button"
            className={SECONDARY}
            disabled={accept.isPending}
            onClick={() => {
              accept.mutate();
            }}
          >
            Aceptar todas las propuestas
          </button>
        )}
        {review.pending === 0 ? (
          <Link
            to={`/juego/${game}/resultado`}
            className="rounded bg-red-700 px-4 py-2 font-semibold text-white hover:bg-red-800"
          >
            Generar el equipo
          </Link>
        ) : (
          <span className="text-sm text-slate-600">
            Cuando todos estén confirmados, podrás generar el equipo.
          </span>
        )}
      </div>
      {accept.error !== null && <ErrorMessage error={accept.error} />}
    </section>
  );
}

function question(fact: ReviewFact, gameName: string): string {
  switch (fact.kind) {
    case "mechanic":
      return `¿${gameName} tiene esta mecánica?`;
    case "exists":
      return `¿Se puede tener ${fact.name} en ${gameName}?`;
    case "arrival":
      return `¿Puede llegar a ${gameName} y evolucionar hasta ${fact.name} antes de completarlo?`;
    case "key_battle":
      return `¿Cuál es el equipo de ${fact.name}?`;
  }
}

function yesNo(value: boolean): string {
  return value ? "Sí" : "No";
}

function Status({ fact }: { fact: ReviewFact }) {
  const [text, style] =
    fact.status === "confirmed"
      ? ["Confirmado", "bg-green-100 text-green-900"]
      : fact.outdated
        ? ["Desactualizado", "bg-amber-100 text-amber-900"]
        : ["Pendiente", "bg-slate-100 text-slate-800"];
  return <span className={`rounded px-2 py-0.5 text-xs font-semibold ${style}`}>{text}</span>;
}

function FactCard({ game, gameName, fact }: { game: string; gameName: string; fact: ReviewFact }) {
  const title = fact.kind === "key_battle" ? `Equipo de ${fact.name}` : fact.name;
  return (
    <li
      aria-label={title}
      className="space-y-2 rounded-lg border border-slate-200 bg-white p-4 shadow-sm"
    >
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-semibold">{title}</h3>
        <Status fact={fact} />
      </div>
      <p className="text-slate-700">{question(fact, gameName)}</p>
      {fact.kind === "key_battle" ? (
        <KeyBattleFact game={game} fact={fact} />
      ) : (
        <BooleanFact game={game} fact={fact} />
      )}
    </li>
  );
}

function BooleanFact({ game, fact }: { game: string; fact: ReviewFact }) {
  const confirm = useConfirmFact(game);
  const proposal = typeof fact.proposal === "boolean" ? fact.proposal : null;
  const value = typeof fact.value === "boolean" ? fact.value : null;
  const confirmed = fact.status === "confirmed" ? value : null;
  return (
    <>
      <p className="text-sm text-slate-600">
        {proposal === null
          ? "Sin propuesta: indica tú la respuesta."
          : `Propuesta: ${yesNo(proposal)}.`}
      </p>
      {fact.outdated && value !== null && (
        <p className="text-sm text-amber-900">
          {`Lo confirmaste como «${yesNo(value)}», pero la carga actual propone otra cosa: vuelve a confirmarlo.`}
        </p>
      )}
      <div role="group" aria-label="Respuesta" className="flex gap-2">
        {[true, false].map((answer) => (
          <button
            key={String(answer)}
            type="button"
            aria-pressed={confirmed === answer}
            disabled={confirm.isPending}
            className={confirmed === answer ? PRIMARY : SECONDARY}
            onClick={() => {
              confirm.mutate({ factKey: fact.fact_key, value: answer });
            }}
          >
            {yesNo(answer)}
          </button>
        ))}
      </div>
      {confirm.error !== null && <ErrorMessage error={confirm.error} />}
    </>
  );
}

function KeyBattleFact({ game, fact }: { game: string; fact: ReviewFact }) {
  const confirm = useConfirmFact(game);
  const [editing, setEditing] = useState(false);
  const proposal = Array.isArray(fact.proposal) ? fact.proposal : null;
  const value = Array.isArray(fact.value) ? fact.value : null;
  const shown = fact.status === "confirmed" ? value : proposal;

  return (
    <>
      {shown === null ? (
        <p className="text-sm text-slate-600">Sin propuesta: indica tú su equipo.</p>
      ) : (
        <div className="text-sm">
          <p className="text-slate-600">
            {fact.status === "confirmed" ? "Equipo confirmado:" : "Equipo propuesto:"}
          </p>
          <Team members={shown} />
        </div>
      )}
      {fact.outdated && value !== null && (
        <div className="text-sm text-amber-900">
          <p>
            Lo confirmaste con este equipo, pero la carga actual propone otro: vuelve a confirmarlo.
          </p>
          <Team members={value} />
        </div>
      )}
      {editing ? (
        <KeyBattleEditor
          initial={value ?? proposal ?? []}
          saving={confirm.isPending}
          onCancel={() => {
            setEditing(false);
            confirm.reset();
          }}
          onSave={(team) => {
            confirm.mutate(
              { factKey: fact.fact_key, value: team },
              {
                onSuccess: () => {
                  setEditing(false);
                },
              },
            );
          }}
        />
      ) : (
        <div className="flex flex-wrap gap-2">
          {fact.status === "pending" && proposal !== null && (
            <button
              type="button"
              className={PRIMARY}
              disabled={confirm.isPending}
              onClick={() => {
                confirm.mutate({ factKey: fact.fact_key, value: proposal });
              }}
            >
              Confirmar el equipo propuesto
            </button>
          )}
          <button
            type="button"
            className={SECONDARY}
            onClick={() => {
              setEditing(true);
            }}
          >
            {shown === null ? "Indicar el equipo" : "Corregir el equipo"}
          </button>
        </div>
      )}
      {confirm.error !== null && <ErrorMessage error={confirm.error} />}
    </>
  );
}

function Team({ members }: { members: readonly string[] }) {
  const names = usePokemonNames();
  return (
    <ol aria-label="Equipo" className="mt-1 flex flex-wrap gap-1">
      {members.map((pokemon, index) => (
        <li key={`${String(index)}-${pokemon}`} className="rounded bg-slate-100 px-2 py-0.5">
          {names.data?.get(pokemon) ?? pokemon}
        </li>
      ))}
    </ol>
  );
}

interface KeyBattleEditorProps {
  initial: readonly string[];
  saving: boolean;
  onSave: (team: string[]) => void;
  onCancel: () => void;
}

function KeyBattleEditor({ initial, saving, onSave, onCancel }: KeyBattleEditorProps) {
  const [team, setTeam] = useState<string[]>([...initial]);
  return (
    <div className="space-y-3 rounded border border-slate-200 p-3">
      <TeamEditor team={team} onChange={setTeam} label="Equipo corregido" />
      <div className="flex gap-2">
        <button
          type="button"
          className={PRIMARY}
          disabled={saving || team.length === 0}
          onClick={() => {
            onSave(team);
          }}
        >
          Guardar el equipo
        </button>
        <button type="button" className={SECONDARY} onClick={onCancel}>
          Cancelar
        </button>
      </div>
    </div>
  );
}
