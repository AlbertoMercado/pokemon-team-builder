import { formatDate, formatDexNumber, shortCommit, todayIso } from "./format";

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

describe("formatDexNumber", () => {
  it("pads the number to three digits", () => {
    expect(formatDexNumber(25)).toBe("#025");
    expect(formatDexNumber(386)).toBe("#386");
  });
});

describe("todayIso", () => {
  it("writes the local date as the API does", () => {
    expect(todayIso(new Date(2026, 9, 5, 23, 30))).toBe("2026-10-05");
  });
});
