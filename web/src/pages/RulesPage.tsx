/**
 * Reglas (RF-06, RF-07): the rules of the catalogue grouped by kind. The hard and presence
 * rules have a switch if they are configurable; the soft ones, a switch and a weight from 0 to
 * 10; the mechanisms are shown as information. Each one with its description and a link to the
 * business rules of the DDF. Every change is saved at once and refreshes the generations.
 */
import { useRules, useUpdateRule } from "../api/queries/rules";
import type { Rule } from "../api/types";
import ErrorMessage from "../components/ErrorMessage";
import { BUSINESS_RULES_URL } from "../lib/docs";

const WEIGHTS = Array.from({ length: 11 }, (_, weight) => weight);

const GROUPS: { kind: Rule["kind"]; title: string; text: string }[] = [
  {
    kind: "hard",
    title: "Reglas duras",
    text: "Filtros: un Pokémon o un equipo que no las cumple se descarta. Las estructurales están siempre activas.",
  },
  {
    kind: "presence",
    title: "Reglas de presencia",
    text: "Obligan a incluir un tipo de miembro en el equipo; si ningún favorito la cumple, se reserva un hueco con sugerencias, salvo la del inicial, que elige ella misma uno de los iniciales del juego.",
  },
  {
    kind: "soft",
    title: "Reglas blandas",
    text: "Puntúan el equipo: cada una aporta su puntuación multiplicada por su peso, de 0 a 10, y se recomiendan los equipos con más puntos.",
  },
  {
    kind: "mechanism",
    title: "Mecanismos",
    text: "Cómo funciona el generador. No se pueden cambiar.",
  },
];

export default function RulesPage() {
  const rules = useRules();
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">Reglas</h1>
        <p className="text-slate-700">
          Decide qué reglas se aplican al generar tus equipos y cuánto pesa cada una. Los cambios se
          guardan al momento y valen para todos los juegos. Cada regla se explica con detalle en las{" "}
          <a href={BUSINESS_RULES_URL} className="text-red-700 underline">
            reglas de negocio
          </a>
          .
        </p>
      </div>
      {rules.error !== null ? (
        <ErrorMessage error={rules.error} />
      ) : rules.data === undefined ? (
        <p className="text-slate-500">Cargando…</p>
      ) : (
        GROUPS.map(({ kind, title, text }) => (
          <section key={kind} aria-label={title} className="space-y-3">
            <h2 className="text-lg font-semibold">{title}</h2>
            <p className="text-sm text-slate-600">{text}</p>
            <ul className="space-y-2">
              {rules.data
                .filter((rule) => rule.kind === kind)
                .map((rule) => (
                  <RuleCard key={rule.rule_id} rule={rule} />
                ))}
            </ul>
          </section>
        ))
      )}
    </div>
  );
}

function RuleCard({ rule }: { rule: Rule }) {
  const update = useUpdateRule();
  const soft = rule.kind === "soft";
  return (
    <li
      aria-label={`${rule.rule_id} ${rule.name}`}
      className={`space-y-2 rounded-lg border bg-white p-3 shadow-sm ${
        rule.enabled ? "border-slate-200" : "border-slate-200 opacity-75"
      }`}
    >
      <div className="flex flex-wrap items-start gap-x-4 gap-y-2">
        <div className="min-w-0 grow">
          <p className="font-medium">
            <span className="font-mono text-xs text-slate-500">{rule.rule_id}</span> {rule.name}
          </p>
          <p className="text-sm text-slate-700">{rule.description}</p>
        </div>
        {rule.kind === "mechanism" ? null : rule.configurable ? (
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              role="switch"
              checked={rule.enabled}
              disabled={update.isPending}
              onChange={(event) => {
                update.mutate({ ruleId: rule.rule_id, change: { enabled: event.target.checked } });
              }}
            />
            Activa
          </label>
        ) : (
          <span className="text-sm text-slate-600">Siempre activa</span>
        )}
        {soft && rule.weight !== null && (
          <label className="flex items-center gap-2 text-sm">
            Peso
            <select
              className="rounded border border-slate-300 bg-white px-2 py-1"
              value={rule.weight}
              disabled={update.isPending}
              onChange={(event) => {
                update.mutate({
                  ruleId: rule.rule_id,
                  change: { weight: Number(event.target.value) },
                });
              }}
            >
              {WEIGHTS.map((weight) => (
                <option key={weight} value={weight}>
                  {weight}
                </option>
              ))}
            </select>
            {rule.default_weight !== null && (
              <span className="text-slate-500">{`(por defecto, ${String(rule.default_weight)})`}</span>
            )}
          </label>
        )}
      </div>
      {update.error !== null && <ErrorMessage error={update.error} />}
    </li>
  );
}
