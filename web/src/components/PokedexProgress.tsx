/**
 * The progress of a Pokédex (RN-22): a bar with the percentage, how many are registered, its
 * state and the impossible ones apart. The API computes it; this only shows it.
 */
import type { PokedexProgress as Progress } from "../api/types";

const STATUS: Readonly<Record<Progress["status"], string>> = {
  not_started: "No iniciada",
  in_progress: "En curso",
  completed: "Completada",
};

export default function PokedexProgress({ progress }: { progress: Progress }) {
  const { registered, total, impossible, percent, status } = progress;
  return (
    <div className="space-y-1">
      <div
        role="progressbar"
        aria-label="Progreso de la Pokédex"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        className="h-2 w-full max-w-sm overflow-hidden rounded bg-slate-200"
      >
        <div className="h-full bg-red-700" style={{ width: `${String(percent)}%` }} />
      </div>
      <p className="text-sm text-slate-700">
        <span className="font-semibold">{`${String(percent)} %`}</span>
        {` · ${String(registered)} de ${String(total)} registrados · ${STATUS[status]}`}
        {impossible > 0 &&
          ` · ${String(impossible)} ${impossible === 1 ? "imposible" : "imposibles"}`}
      </p>
    </div>
  );
}
