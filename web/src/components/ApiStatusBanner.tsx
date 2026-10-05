/**
 * Notice for the whole application when it cannot work: no reference data loaded (`503`) or
 * the API does not answer. It follows `GET /api/meta`, which every screen shares.
 */
import type { ReactNode } from "react";

import { ApiError, NetworkError } from "../api/client";
import { useMeta } from "../api/queries/meta";
import { LOAD_COMMAND, START_COMMAND } from "../lib/commands";

export default function ApiStatusBanner() {
  const { error } = useMeta();
  if (error instanceof NetworkError) {
    return (
      <Banner title="La API no responde">
        Arráncala desde la raíz del proyecto con <Command>{START_COMMAND}</Command> y vuelve a
        cargar la página.
      </Banner>
    );
  }
  if (error instanceof ApiError && error.status === 503) {
    return (
      <Banner title="No hay datos cargados">
        Ejecuta la carga de datos con <Command>{LOAD_COMMAND}</Command> y reinicia la API.
      </Banner>
    );
  }
  return null;
}

function Banner({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div role="alert" className="border-b border-amber-300 bg-amber-50">
      <div className="mx-auto max-w-5xl px-4 py-3 text-amber-950">
        <p className="font-semibold">{title}</p>
        <p>{children}</p>
      </div>
    </div>
  );
}

function Command({ children }: { children: string }) {
  return <code className="rounded bg-amber-100 px-1 font-mono text-sm">{children}</code>;
}
