/**
 * Who owns the images and where the data comes from (CA-56, ADR-0004, ADR-0010). Shown at the
 * foot of every screen.
 */
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
