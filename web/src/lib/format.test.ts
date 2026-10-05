import { formatDate, shortCommit } from "./format";

describe("formatDate", () => {
  it("writes a date of the API in Spanish without moving it to another day", () => {
    expect(formatDate("2026-10-04")).toBe("4 de octubre de 2026");
  });
});

describe("shortCommit", () => {
  it("keeps the first 7 characters of a commit", () => {
    expect(shortCommit("bc92d3b" + "6029ef1abe9e")).toBe("bc92d3b");
  });
});
