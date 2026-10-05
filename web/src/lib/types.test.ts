import { TYPE_IDS, typeStyle } from "./types";

describe("typeStyle", () => {
  it("has the 18 types with their Spanish name", () => {
    expect(TYPE_IDS).toHaveLength(18);
    expect(typeStyle("fire").name).toBe("Fuego");
    expect(typeStyle("dark").name).toBe("Siniestro");
  });

  it("shows an unknown type with its identifier", () => {
    expect(typeStyle("stellar").name).toBe("stellar");
  });
});
