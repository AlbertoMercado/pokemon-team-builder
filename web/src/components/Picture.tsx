/**
 * A decorative image next to a name: the images of the Pokémon (RF-17) and the covers of the
 * games (RF-18). The name beside it identifies what it shows, also for screen readers, so the
 * image has `alt=""`. Without `url`, or if it does not load, `fallback` is shown instead
 * (nothing by default) and the name stands alone.
 *
 * The image sits in a square box of a fixed size and is scaled to fit in it, centred and
 * without distortion, so every row has the same height whatever the shape of the image. The
 * box is set in CSS because Tailwind's base styles give images `height: auto`, which overrides
 * the `height` attribute (#65).
 */
import { useState, type ReactNode } from "react";

/** Pixels for the width and height attributes, and the Tailwind class of the same box. */
export interface PictureSize {
  pixels: number;
  box: string;
}

interface PictureProps {
  url: string | null | undefined;
  size: PictureSize;
  className?: string;
  fallback?: ReactNode;
}

export default function Picture({ url, size, className = "", fallback = null }: PictureProps) {
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
