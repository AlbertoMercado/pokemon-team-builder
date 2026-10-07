/**
 * Client of the API, typed with the contract generated from its OpenAPI (ADR-0007).
 *
 * `api` makes the calls; `unwrap` turns an error answer into an `ApiError` and `api` turns a
 * failed connection into a `NetworkError`, so every query fails with one of the two and the
 * screens show it as the design says (docs/02-ddt/web.md, "Cómo se muestran los errores").
 */
import createClient from "openapi-fetch";

import type { paths } from "./schema";

/** The API answered with an error (`404`, `409`, `422`, `503`…). */
export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, detail: unknown) {
    super(detailMessage(detail) ?? `La API respondió con el error ${String(status)}.`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

/** The API did not answer: it is not running or the connection failed. */
export class NetworkError extends Error {
  constructor(cause: unknown) {
    super("La API no responde.", { cause });
    this.name = "NetworkError";
  }
}

/** The message of a `detail`: a text, an object with `message` (409) or validation errors (422). */
export function detailMessage(detail: unknown): string | undefined {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item: unknown) => (isRecord(item) && typeof item.msg === "string" ? item.msg : null))
      .filter((message) => message !== null);
    return messages.length > 0 ? messages.join(". ") : undefined;
  }
  if (isRecord(detail) && typeof detail.message === "string") {
    return detail.message;
  }
  return undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** No reference data loaded (`503`) or no API: the whole application is affected. */
export function isUnavailable(error: unknown): boolean {
  return error instanceof NetworkError || (error instanceof ApiError && error.status === 503);
}

export const api = createClient<paths>({
  // The paths of the contract already start with /api: same origin as the web.
  baseUrl: globalThis.location.origin,
  // Read globalThis.fetch on every call, not once, so the tests can intercept it (MSW).
  fetch: async (request) => {
    try {
      return await globalThis.fetch(request);
    } catch (error) {
      throw new NetworkError(error);
    }
  },
});

interface Result<T> {
  data?: T;
  error?: unknown;
  response: Response;
}

/** The data of a successful answer; an `ApiError` with its `detail` otherwise. */
export function unwrap<T>({ data, error, response }: Result<T>): T {
  if (!response.ok) {
    const detail = isRecord(error) ? error.detail : undefined;
    throw new ApiError(response.status, detail);
  }
  return data as T;
}
