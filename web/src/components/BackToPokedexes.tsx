/** The link back to the list of Pokédexes, when a Pokédex fails or from its screens. */
import { Link } from "react-router";

export default function BackToPokedexes() {
  return (
    <Link to="/pokedex" className="text-sm text-red-700 underline">
      Volver a las Pokédex
    </Link>
  );
}
