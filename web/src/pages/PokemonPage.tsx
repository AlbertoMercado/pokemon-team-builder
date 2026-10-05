/**
 * Ficha (RF-02, RF-03): number, name, current types, the star and the evolutionary line by
 * stage with how each form evolves, in text (lib/evolution.ts). The line links to the other
 * forms.
 */
import { Link, useParams } from "react-router";

import { usePokemon } from "../api/queries/pokemon";
import type { Evolution, LineMember, PokemonDetail } from "../api/types";
import ErrorMessage from "../components/ErrorMessage";
import FavoriteButton from "../components/FavoriteButton";
import FavoriteHint from "../components/FavoriteHint";
import { TypeBadges } from "../components/TypeBadge";
import { describeMethods } from "../lib/evolution";
import { formatDexNumber } from "../lib/format";

export default function PokemonPage() {
  const { pokemon = "" } = useParams();
  const detail = usePokemon(pokemon);
  if (detail.error !== null) {
    return (
      <div className="space-y-4">
        <ErrorMessage error={detail.error} />
        <BackToCatalog />
      </div>
    );
  }
  if (detail.data === undefined) {
    return <p className="text-slate-500">Cargando…</p>;
  }
  return <Detail detail={detail.data} />;
}

function BackToCatalog() {
  return (
    <Link to="/pokemon" className="text-sm text-red-700 underline">
      Volver al catálogo
    </Link>
  );
}

function Detail({ detail }: { detail: PokemonDetail }) {
  return (
    <div className="space-y-6">
      <BackToCatalog />
      <section className="space-y-2">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono text-slate-500">{formatDexNumber(detail.dex_number)}</span>
          <h1 className="text-2xl font-bold">{detail.name}</h1>
          <FavoriteButton pokemon={detail.pokemon} name={detail.name} favorite={detail.favorite} />
        </div>
        <TypeBadges types={detail.types} />
        <p className="text-sm text-slate-600">
          {`Aparece en la ${String(detail.generation)}.ª generación`}
          {detail.is_legendary && ". Legendario"}
          {detail.is_mythical && ". Singular"}.
        </p>
      </section>
      <Line detail={detail} />
      <FavoriteHint />
    </div>
  );
}

function Line({ detail }: { detail: PokemonDetail }) {
  if (detail.line.length <= 1) {
    return <p>No evoluciona ni tiene preevoluciones.</p>;
  }
  const stages = Map.groupBy(detail.line, (member) => member.stage);
  const names = new Map(detail.line.map((member) => [member.pokemon, member.name]));
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Línea evolutiva</h2>
      <ol className="space-y-3">
        {[...stages].map(([stage, members]) => (
          <li key={stage}>
            <h3 className="text-sm font-semibold text-slate-500">{`Etapa ${String(stage)}`}</h3>
            <ul className="mt-1 space-y-2">
              {members.map((member) => (
                <LineEntry
                  key={member.pokemon}
                  member={member}
                  current={member.pokemon === detail.pokemon}
                  evolutions={detail.evolutions.filter((e) => e.to_pokemon === member.pokemon)}
                  names={names}
                />
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </section>
  );
}

interface LineEntryProps {
  member: LineMember;
  current: boolean;
  evolutions: Evolution[];
  names: Map<string, string>;
}

function LineEntry({ member, current, evolutions, names }: LineEntryProps) {
  return (
    <li className="rounded-lg border border-slate-200 bg-white px-3 py-2">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-mono text-sm text-slate-500">
          {formatDexNumber(member.dex_number)}
        </span>
        <Link
          to={`/pokemon/${member.pokemon}`}
          aria-current={current ? "page" : undefined}
          className={current ? "font-bold text-red-700" : "font-medium hover:text-red-700"}
        >
          {member.name}
        </Link>
        <TypeBadges types={member.types} />
        {member.favorite && <span className="text-sm text-amber-600">★ Favorito</span>}
      </div>
      {evolutions.map((evolution) => (
        <p key={evolution.from_pokemon} className="mt-1 text-sm text-slate-700">
          {`Desde ${names.get(evolution.from_pokemon) ?? evolution.from_pokemon}: `}
          {describeMethods(evolution.methods)}
        </p>
      ))}
    </li>
  );
}
