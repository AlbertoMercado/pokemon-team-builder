/** Page shown for an address that does not match any screen. */
import { Link } from "react-router";

export default function NotFoundPage() {
  return (
    <section>
      <h1 className="text-2xl font-bold">Página no encontrada</h1>
      <p className="mt-2 text-slate-700">
        Esta dirección no existe.{" "}
        <Link to="/" className="text-red-700 underline">
          Volver al inicio
        </Link>
        .
      </p>
    </section>
  );
}
