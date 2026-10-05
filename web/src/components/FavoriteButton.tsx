/**
 * The star that adds a form to the favourites or removes it (RF-03). The change refreshes
 * every screen that shows it: catalogue, detail and favourites.
 */
import { useSetFavorite } from "../api/queries/favorites";
import ErrorMessage from "./ErrorMessage";

interface Props {
  pokemon: string;
  name: string;
  favorite: boolean;
}

export default function FavoriteButton({ pokemon, name, favorite }: Props) {
  const setFavorite = useSetFavorite();
  const label = favorite ? `Quitar ${name} de favoritos` : `Añadir ${name} a favoritos`;
  return (
    <span className="inline-flex items-center gap-2">
      <button
        type="button"
        aria-label={label}
        aria-pressed={favorite}
        title={label}
        disabled={setFavorite.isPending}
        onClick={() => {
          setFavorite.mutate({ pokemon, favorite: !favorite });
        }}
        className={`rounded px-1 text-2xl leading-none disabled:opacity-50 ${
          favorite ? "text-amber-500 hover:text-amber-600" : "text-slate-300 hover:text-amber-500"
        }`}
      >
        {favorite ? "★" : "☆"}
      </button>
      {setFavorite.error !== null && <ErrorMessage error={setFavorite.error} />}
    </span>
  );
}
