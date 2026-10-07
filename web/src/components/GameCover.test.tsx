import { fireEvent, render } from "@testing-library/react";

import GameCover from "./GameCover";

describe("Portada de un juego (RF-18)", () => {
  it("is a decorative image of a fixed size that loads lazily", () => {
    const { container } = render(<GameCover url="/api/games/firered/cover" size="large" />);
    const image = container.querySelector("img");

    expect(image).toHaveAttribute("src", "/api/games/firered/cover");
    // The name of the game beside it identifies it: screen readers do not read the image.
    expect(image).toHaveAttribute("alt", "");
    expect(image).toHaveAttribute("width", "96");
    expect(image).toHaveAttribute("height", "96");
    expect(image).toHaveAttribute("loading", "lazy");
  });

  it("fits covers of any proportion in a square box without distortion (#65)", () => {
    const { container } = render(<GameCover url="/api/games/emerald/cover" />);
    const image = container.querySelector("img");

    expect(image).toHaveClass("size-16", "max-w-none", "object-contain");
    // Covers are photographs, not pixel art.
    expect(image?.className).not.toContain("pixelated");
  });

  it("shows nothing when the game has no cover", () => {
    const { container } = render(<GameCover url={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("hides itself when the cover does not load", () => {
    const { container } = render(<GameCover url="/api/games/firered/cover" />);
    fireEvent.error(container.querySelector("img") as HTMLImageElement);
    expect(container).toBeEmptyDOMElement();
  });
});
