/**
 * Who owns the images and where the data comes from (CA-56, ADR-0004, ADR-0010, ADR-0011).
 * Shown at the foot of every screen.
 *
 * The covers of the games are fair use only in the WikiDex articles, so they are used in
 * private and each one links to its page there (ADR-0011). The paragraph about them only
 * appears if some loaded game has a cover: a load with `--no-covers` shows none.
 */
import { useGames } from "../api/queries/games";

export default function ImageNotice() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-5xl space-y-1 px-4 py-3 text-xs text-slate-500">
        <p>
          Las imágenes de los Pokémon son © Nintendo, Creatures, GAME FREAK y The Pokémon Company.
          Se obtienen del repositorio de imágenes de{" "}
          <a className="underline hover:text-red-700" href="https://github.com/PokeAPI/sprites">
            PokeAPI
          </a>{" "}
          y se guardan solo en la caché local de la aplicación, sin redistribuirlas.
        </p>
        <CoversNotice />
        <p>
          Datos de{" "}
          <a className="underline hover:text-red-700" href="https://pokeapi.co/">
            PokeAPI
          </a>{" "}
          y equipos de los combates clave de{" "}
          <a className="underline hover:text-red-700" href="https://www.wikidex.net/">
            WikiDex
          </a>{" "}
          (
          <a
            className="underline hover:text-red-700"
            href="https://creativecommons.org/licenses/by-nc-sa/3.0/deed.es"
          >
            CC BY-NC-SA 3.0
          </a>
          ). Aplicación personal y sin ánimo de lucro, sin relación con Nintendo ni The Pokémon
          Company.
        </p>
      </div>
    </footer>
  );
}

function CoversNotice() {
  const games = useGames({ all: true });
  const covers = (games.data ?? []).flatMap((game) =>
    game.cover_url !== null && game.cover_source_url !== null
      ? [{ game: game.game, name: game.name, source: game.cover_source_url }]
      : [],
  );
  if (covers.length === 0) {
    return null;
  }
  return (
    <p>
      Las portadas de los juegos son © Nintendo, Creatures, GAME FREAK y The Pokémon Company. Se
      obtienen de WikiDex, que las declara de uso legítimo solo en sus artículos, así que la
      aplicación las usa solo en privado. Páginas en WikiDex:{" "}
      {covers.map((cover, index) => (
        <span key={cover.game}>
          {index > 0 && ", "}
          <a className="underline hover:text-red-700" href={cover.source}>
            {`portada de ${cover.name}`}
          </a>
        </span>
      ))}
      .
    </p>
  );
}
