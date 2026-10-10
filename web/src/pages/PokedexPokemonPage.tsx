/**
 * The card of any Pokémon of a Pokédex (RF-22, RF-23): where the card of the objective or the
 * detail link to, for example to see how to obtain the Pokémon to evolve or breed from
 * (CA-76). The same card and actions as the objective, without skipping.
 */
import { Link, useParams } from "react-router";

import { usePokedexPokemon } from "../api/queries/pokedex";
import ErrorMessage from "../components/ErrorMessage";
import PokedexCard from "../components/PokedexCard";

export default function PokedexPokemonPage() {
  const { game = "", species = "" } = useParams();
  const pokemon = usePokedexPokemon(game, species);
  return (
    <div className="space-y-4">
      <Link to={`/pokedex/${game}`} className="text-sm text-red-700 underline">
        Volver a la Pokédex
      </Link>
      {pokemon.error !== null ? (
        <ErrorMessage error={pokemon.error} />
      ) : pokemon.data === undefined ? (
        <p className="text-slate-500">Cargando…</p>
      ) : (
        <PokedexCard game={game} pokemon={pokemon.data} />
      )}
    </div>
  );
}
