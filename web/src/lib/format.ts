/** Values of the API shown to the user: dates in Spanish, Pokédex numbers and commits. */

const DATE = new Intl.DateTimeFormat("es-ES", { dateStyle: "long", timeZone: "UTC" });
const DATE_TIME = new Intl.DateTimeFormat("es-ES", { dateStyle: "long", timeStyle: "short" });

/** A date without time (`2026-10-04`), the same in every time zone: «4 de octubre de 2026». */
export function formatDate(isoDate: string): string {
  return DATE.format(new Date(`${isoDate}T00:00:00Z`));
}

/** An instant (`2026-10-04T10:00:00Z`) in the local time of the user. */
export function formatDateTime(isoDateTime: string): string {
  return DATE_TIME.format(new Date(isoDateTime));
}

const SHORT_COMMIT = 7;

/** The first characters of a commit, as Git shows it: `bc92d3b`. */
export function shortCommit(commit: string): string {
  return commit.slice(0, SHORT_COMMIT);
}

/** A National Pokédex number with three digits at least: `#025`. */
export function formatDexNumber(number: number): string {
  return `#${String(number).padStart(3, "0")}`;
}
