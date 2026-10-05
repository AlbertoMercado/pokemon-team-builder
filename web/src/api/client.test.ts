import { http, HttpResponse } from "msw";

import { server, withoutApi } from "../test/server";
import { api, ApiError, detailMessage, isUnavailable, NetworkError, unwrap } from "./client";

describe("detailMessage", () => {
  it("returns a text detail as it is", () => {
    expect(detailMessage("No existe el Pokémon «mew»")).toBe("No existe el Pokémon «mew»");
  });

  it("returns the message of a 409 with extra fields", () => {
    expect(detailMessage({ message: "Faltan datos por confirmar", pending: 3 })).toBe(
      "Faltan datos por confirmar",
    );
  });

  it("joins the messages of the validation errors of a 422", () => {
    const detail = [
      { loc: ["body", "members"], msg: "List should have at least 1 item", type: "too_short" },
      { loc: ["body", "game"], msg: "Field required", type: "missing" },
    ];
    expect(detailMessage(detail)).toBe("List should have at least 1 item. Field required");
  });

  it("has no message for an unknown detail", () => {
    expect(detailMessage(undefined)).toBeUndefined();
    expect(detailMessage({ code: 1 })).toBeUndefined();
  });
});

describe("unwrap", () => {
  it("returns the data of a successful answer", async () => {
    const meta = unwrap(await api.GET("/api/meta"));
    expect(meta.app_version).toBe("0.9.0");
  });

  it("throws an ApiError with the status and the message of the detail", async () => {
    server.use(
      http.get("/api/meta", () =>
        HttpResponse.json({ detail: "No hay datos de referencia" }, { status: 503 }),
      ),
    );
    const error = await getMetaError();
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 503, message: "No hay datos de referencia" });
    expect(isUnavailable(error)).toBe(true);
  });

  it("gives a generic message when the error has no detail", async () => {
    server.use(http.get("/api/meta", () => new HttpResponse("boom", { status: 500 })));
    const error = await getMetaError();
    expect(error).toMatchObject({ status: 500, message: "La API respondió con el error 500." });
    expect(isUnavailable(error)).toBe(false);
  });

  it("turns a failed connection into a NetworkError", async () => {
    withoutApi();
    const error = await getMetaError();
    expect(error).toBeInstanceOf(NetworkError);
    expect(isUnavailable(error)).toBe(true);
  });
});

async function getMetaError(): Promise<unknown> {
  try {
    unwrap(await api.GET("/api/meta"));
  } catch (error) {
    return error;
  }
  throw new Error("se esperaba un error");
}
