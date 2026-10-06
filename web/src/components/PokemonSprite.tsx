/**
 * The images of a form, next to its name (RF-17). They are decorative (`alt=""`): the name
 * beside them identifies the Pokémon, also for screen readers.
 *
 * - `PokemonSprite`: its sprite trimmed to the figure, for the lists. Without `url`, or if it
 *   does not load, nothing is shown and the name stands alone.
 * - `PokemonArtwork`: its official artwork, larger, for the detail. Without it, or if it does
 *   not load, its sprite is shown instead.
 */
import { useState, type ReactNode } from "react";

const SIZES = { small: 40, medium: 64, large: 128 } as const;
const ARTWORK_SIZE = 160;

interface PictureProps {
  url: string | null | undefined;
  pixels: number;
  className: string;
  fallback?: ReactNode;
}

function Picture({ url, pixels, className, fallback = null }: PictureProps) {
  const [failed, setFailed] = useState<string | null>(null);
  if (!url || failed === url) {
    return fallback;
  }
  return (
    <img
      src={url}
      alt=""
      width={pixels}
      height={pixels}
      loading="lazy"
      decoding="async"
      className={`shrink-0 object-contain ${className}`}
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
  return <Picture url={url} pixels={SIZES[size]} className="[image-rendering:pixelated]" />;
}

interface ArtworkProps {
  url: string | null | undefined;
  spriteUrl: string | null | undefined;
}

export function PokemonArtwork({ url, spriteUrl }: ArtworkProps) {
  return (
    <Picture
      url={url}
      pixels={ARTWORK_SIZE}
      className=""
      fallback={<PokemonSprite url={spriteUrl} size="large" />}
    />
  );
}
