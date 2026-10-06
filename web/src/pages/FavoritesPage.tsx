/** Favoritos (RF-04): the list with its total, and the star to remove each one. */
import { Link } from "react-router";

import { useFavorites } from "../api/queries/favorites";
import ErrorMessage from "../components/ErrorMessage";
import FavoriteButton from "../components/FavoriteButton";
import FavoriteHint from "../components/FavoriteHint";
import PokemonName from "../components/PokemonName";
import { TypeBadges } from "../components/TypeBadge";

export default function FavoritesPage() {
  const favorites = useFavorites();
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Favoritos</h1>
      <FavoriteHint />
      {favorites.error !== null ? (
        <ErrorMessage error={favorites.error} />
      ) : favorites.data === undefined ? (
        <p className="text-slate-500">Cargando…</p>
      ) : favorites.data.total === 0 ? (
        <p>
          Todavía no tienes favoritos. Añádelos desde el{" "}
          <Link to="/pokemon" className="text-red-700 underline">
            catálogo
          </Link>
          .
        </p>
      ) : (
        <section aria-label="Lista de favoritos">
          <p className="mb-2 text-sm text-slate-600">
            {favorites.data.total === 1
              ? "1 favorito"
              : `${String(favorites.data.total)} favoritos`}
          </p>
          <ul
            aria-label="Favoritos"
            className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white"
          >
            {favorites.data.favorites.map((favorite) => (
              <li key={favorite.pokemon} className="flex flex-wrap items-center gap-3 px-3 py-2">
                <PokemonName
                  pokemon={favorite.pokemon}
                  name={favorite.name}
                  dexNumber={favorite.dex_number}
                  imageUrl={favorite.image_url}
                />
                <TypeBadges types={favorite.types} />
                <span className="ml-auto">
                  <FavoriteButton pokemon={favorite.pokemon} name={favorite.name} favorite />
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
