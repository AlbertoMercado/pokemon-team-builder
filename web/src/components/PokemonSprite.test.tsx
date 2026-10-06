import { fireEvent, render } from "@testing-library/react";

import PokemonSprite, { PokemonArtwork } from "./PokemonSprite";

describe("Imagen de un Pokémon (RF-17)", () => {
  it("is a decorative image of a fixed size that loads lazily", () => {
    const { container } = render(<PokemonSprite url="/api/pokemon/vulpix/image" size="large" />);
    const image = container.querySelector("img");

    expect(image).toHaveAttribute("src", "/api/pokemon/vulpix/image");
    // The name beside it identifies the Pokémon: screen readers do not read the image.
    expect(image).toHaveAttribute("alt", "");
    expect(image).toHaveAttribute("width", "128");
    expect(image).toHaveAttribute("height", "128");
    expect(image).toHaveAttribute("loading", "lazy");
  });

  it("shows nothing when the form has no image", () => {
    const { container } = render(<PokemonSprite url={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("hides itself when the image does not load", () => {
    const { container } = render(<PokemonSprite url="/api/pokemon/vulpix/image" />);
    fireEvent.error(container.querySelector("img") as HTMLImageElement);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("Ilustración de un Pokémon (RF-17)", () => {
  it("is a decorative image that is not pixelated", () => {
    const { container } = render(
      <PokemonArtwork url="/api/pokemon/vulpix/artwork" spriteUrl="/api/pokemon/vulpix/image" />,
    );
    const image = container.querySelector("img");

    expect(image).toHaveAttribute("src", "/api/pokemon/vulpix/artwork");
    expect(image).toHaveAttribute("alt", "");
    expect(image).toHaveAttribute("width", "160");
    expect(image?.className).not.toContain("pixelated");
  });

  it("shows the sprite when the form has no artwork or it does not load", () => {
    const { container, rerender } = render(
      <PokemonArtwork url={null} spriteUrl="/api/pokemon/vulpix/image" />,
    );
    expect(container.querySelector("img")).toHaveAttribute("src", "/api/pokemon/vulpix/image");

    rerender(
      <PokemonArtwork url="/api/pokemon/vulpix/artwork" spriteUrl="/api/pokemon/vulpix/image" />,
    );
    fireEvent.error(container.querySelector("img") as HTMLImageElement);
    expect(container.querySelector("img")).toHaveAttribute("src", "/api/pokemon/vulpix/image");
  });
});
