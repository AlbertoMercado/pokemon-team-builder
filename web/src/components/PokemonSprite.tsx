/**
 * The image of a form, next to its name (RF-17). It is decorative (`alt=""`): the name beside
 * it identifies the Pokémon, also for screen readers. Without `url`, or if the image does not
 * load, nothing is shown and the name stands alone.
 */
import { useState } from "react";

const SIZES = { small: 40, medium: 64, large: 128 } as const;

interface Props {
  url: string | null | undefined;
  size?: keyof typeof SIZES;
}

export default function PokemonSprite({ url, size = "small" }: Props) {
  const [failed, setFailed] = useState<string | null>(null);
  if (!url || failed === url) {
    return null;
  }
  const pixels = SIZES[size];
  return (
    <img
      src={url}
      alt=""
      width={pixels}
      height={pixels}
      loading="lazy"
      decoding="async"
      // Sprites are pixel art: scaled without smoothing they stay sharp.
      className="shrink-0 [image-rendering:pixelated]"
      onError={() => {
        setFailed(url);
      }}
    />
  );
}
