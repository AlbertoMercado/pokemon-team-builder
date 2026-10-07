/**
 * The cover of a game, next to its name (RF-18). Like the images of the Pokémon it is
 * decorative (`alt=""`) and, without `url` or if it does not load, nothing is shown and the
 * name stands alone. Covers have slightly different proportions: each one is scaled to fit in
 * a square box of a fixed size.
 *
 * The covers come from WikiDex and are for private use only (ADR-0011): the notice at the foot
 * of every screen (`ImageNotice`) says who owns them and links to the page of each one.
 */
import Picture from "./Picture";

const SIZES = {
  small: { pixels: 40, box: "size-10" },
  medium: { pixels: 64, box: "size-16" },
  large: { pixels: 96, box: "size-24" },
} as const;

interface GameCoverProps {
  url: string | null | undefined;
  size?: keyof typeof SIZES;
}

export default function GameCover({ url, size = "medium" }: GameCoverProps) {
  return <Picture url={url} size={SIZES[size]} className="rounded-sm" />;
}
