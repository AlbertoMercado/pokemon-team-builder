/** Placeholder of a screen of a later phase of the plan of the web. */
export default function PendingPage({ title }: { title: string }) {
  return (
    <section>
      <h1 className="text-2xl font-bold">{title}</h1>
      <p className="mt-2 text-slate-700">Esta pantalla todavía no está disponible.</p>
    </section>
  );
}
