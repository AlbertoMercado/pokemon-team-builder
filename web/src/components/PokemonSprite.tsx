/**
 * The images of a form, next to its name (RF-17). They are decorative (`alt=""`): the name
 * beside them identifies the Pokémon, also for screen readers.
 *
 * - `PokemonSprite`: its sprite trimmed to the figure, for the lists. Without `url`, or if it
 *   does not load, nothing is shown and the name stands alone.
 * - `PokemonArtwork`: its official artwork, larger, for the detail. Without it, or if it does
 *   not load, its sprite is shown instead.
 *
 * Each image sits in a square box of a fixed size (`Picture`), so every row has the same
 * height whatever the shape of the Pokémon (#65).
 */
import Picture from "./Picture";

// Pixels for the width and height attributes, and the Tailwind class of the same box.
const SIZES = {
  small: { pixels: 40, box: "size-10" },
  medium: { pixels: 64, box: "size-16" },
  large: { pixels: 128, box: "size-32" },
} as const;
const ARTWORK = { pixels: 160, box: "size-40" } as const;

interface SpriteProps {
  url: string | null | undefined;
  size?: keyof typeof SIZES;
}

export default function PokemonSprite({ url, size = "small" }: SpriteProps) {
  // Sprites are pixel art: scaled without smoothing they stay sharp.
  return <Picture url={url} size={SIZES[size]} className="[image-rendering:pixelated]" />;
}

interface ArtworkProps {
  url: string | null | undefined;
  spriteUrl: string | null | undefined;
}

export function PokemonArtwork({ url, spriteUrl }: ArtworkProps) {
  return (
    <Picture url={url} size={ARTWORK} fallback={<PokemonSprite url={spriteUrl} size="large" />} />
  );
}
