import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";

import PokemonRow from "./PokemonRow";

function renderRow(props: Partial<Parameters<typeof PokemonRow>[0]> = {}) {
  return render(
    <MemoryRouter>
      <PokemonRow
        pokemon="charizard"
        name="Charizard"
        dexNumber={6}
        imageUrl="/api/pokemon/charizard/image"
        types={["fire", "flying"]}
        action={<button type="button">Estrella</button>}
        {...props}
      />
    </MemoryRouter>,
  );
}

describe("Fila de un Pokémon (RF-01, #68)", () => {
  it("shows the image, the number, the name linked to its detail and the types", () => {
    renderRow();

    expect(screen.getByText("#006")).toBeVisible();
    expect(screen.getByRole("link", { name: "Charizard" })).toHaveAttribute(
      "href",
      "/pokemon/charizard",
    );
    expect(
      within(screen.getByRole("list", { name: "Tipos" })).getAllByRole("listitem"),
    ).toHaveLength(2);
  });

  it("keeps the action apart, at the right, so it never wraps to another line", () => {
    const { container } = renderRow();
    const row = container.firstElementChild as HTMLElement;
    const [image, block, action] = Array.from(row.children);

    // Two zones: the image and a block that takes the free space and may shrink…
    expect(row).not.toHaveClass("flex-wrap");
    expect(image?.tagName).toBe("IMG");
    expect(block).toHaveClass("min-w-0", "flex-1");
    expect(within(block as HTMLElement).getByRole("link", { name: "Charizard" })).toBeVisible();
    // …and the action, which never shrinks.
    expect(action).toHaveClass("shrink-0");
    expect(within(action as HTMLElement).getByRole("button", { name: "Estrella" })).toBeVisible();
  });

  it("puts the number and name over the types on narrow screens, in one line from sm", () => {
    const { container } = renderRow();
    const block = container.firstElementChild?.children[1];

    expect(block).toHaveClass("flex-col", "sm:flex-row");
  });

  it("marks the current form and shows the extra marks after the types", () => {
    renderRow({ current: true, extra: <span>★ Favorito</span>, action: undefined });

    expect(screen.getByRole("link", { name: "Charizard" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByText("★ Favorito")).toBeVisible();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
