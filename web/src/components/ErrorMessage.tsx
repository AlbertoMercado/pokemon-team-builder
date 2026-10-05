/** The message of a failed query or action, next to what produced it. */
export default function ErrorMessage({ error }: { error: Error }) {
  return (
    <p role="alert" className="rounded border border-red-200 bg-red-50 px-3 py-2 text-red-800">
      {error.message}
    </p>
  );
}
