/**
 * Editor of a team in order, up to 6: the members with a button to remove each one, and the
 * Pokémon picker to add more at the end. Controlled: `team` and `onChange` belong to the
 * screen, which decides when to save. Used by the key battles of the review and by the Hall of
 * Fame; the API validates the Pokémon.
 */
import { usePokemonNames } from "../api/queries/pokemon";
import PokemonPicker from "./PokemonPicker";

export const TEAM_SIZE = 6;

interface Props {
  team: readonly string[];
  onChange: (team: string[]) => void;
  /** Accessible name of the list of members. */
  label: string;
}

export default function TeamEditor({ team, onChange, label }: Props) {
  const names = usePokemonNames();
  return (
    <div className="space-y-2">
      <p className="text-sm font-semibold">{`Equipo en orden (${String(team.length)} de ${String(TEAM_SIZE)})`}</p>
      {team.length > 0 && (
        <ol aria-label={label} className="space-y-1">
          {team.map((pokemon, index) => {
            const name = names.data?.get(pokemon) ?? pokemon;
            return (
              <li key={`${String(index)}-${pokemon}`} className="flex items-center gap-2 text-sm">
                <span>{`${String(index + 1)}. ${name}`}</span>
                <button
                  type="button"
                  className="text-red-700 underline"
                  onClick={() => {
                    onChange(team.filter((_, position) => position !== index));
                  }}
                >
                  {`Quitar ${name}`}
                </button>
              </li>
            );
          })}
        </ol>
      )}
      <PokemonPicker
        label="Añadir un Pokémon al equipo"
        disabled={team.length >= TEAM_SIZE}
        onPick={(pokemon) => {
          onChange([...team, pokemon.pokemon]);
        }}
      />
    </div>
  );
}
