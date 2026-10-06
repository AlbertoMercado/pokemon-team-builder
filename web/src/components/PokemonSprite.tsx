/**
 * The images of a form, next to its name (RF-17). They are decorative (`alt=""`): the name
 * beside them identifies the Pokémon, also for screen readers.
 *
 * - `PokemonSprite`: its sprite trimmed to the figure, for the lists. Without `url`, or if it
 *   does not load, nothing is shown and the name stands alone.
 * - `PokemonArtwork`: its official artwork, larger, for the detail. Without it, or if it does
 *   not load, its sprite is shown instead.
 *
 * Each image sits in a square box of a fixed size and is scaled to fit in it, centred and
 * without distortion, so every row has the same height whatever the shape of the Pokémon. The
 * box is set in CSS because Tailwind's base styles give images `height: auto`, which overrides
 * the `height` attribute (#65).
 */
import { useState, type ReactNode } from "react";

// Pixels for the width and height attributes, and the Tailwind class of the same box.
const SIZES = {
  small: { pixels: 40, box: "size-10" },
  medium: { pixels: 64, box: "size-16" },
  large: { pixels: 128, box: "size-32" },
} as const;
const ARTWORK = { pixels: 160, box: "size-40" } as const;

interface PictureProps {
  url: string | null | undefined;
  size: { pixels: number; box: string };
  className: string;
  fallback?: ReactNode;
}

function Picture({ url, size, className, fallback = null }: PictureProps) {
  const [failed, setFailed] = useState<string | null>(null);
  if (!url || failed === url) {
    return fallback;
  }
  return (
    <img
      src={url}
      alt=""
      width={size.pixels}
      height={size.pixels}
      loading="lazy"
      decoding="async"
      className={`${size.box} max-w-none shrink-0 object-contain ${className}`}
      onError={() => {
        setFailed(url);
      }}
    />
  );
}

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
    <Picture
      url={url}
      size={ARTWORK}
      className=""
      fallback={<PokemonSprite url={spriteUrl} size="large" />}
    />
  );
}
