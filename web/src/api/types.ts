/** Short names for the schemas of the contract that the screens use. */
import type { components } from "./schema";

type Schemas = components["schemas"];

export type Meta = Schemas["Meta"];
export type FavoritesOut = Schemas["FavoritesOut"];
export type HallOfFameEntry = Schemas["HallOfFameEntryOut"];
export type CatalogPokemon = Schemas["CatalogPokemonOut"];
export type CatalogOut = Schemas["CatalogOut"];
export type PokemonDetail = Schemas["PokemonDetailOut"];
export type LineMember = Schemas["LineMemberOut"];
export type Evolution = Schemas["EvolutionOut"];
export type Game = Schemas["GameOut"];
export type Review = Schemas["ReviewOut"];
export type ReviewFact = Schemas["ReviewFactOut"];
export type ReviewValue = Schemas["ReviewValue"];
export type Generation = Schemas["GenerationOut"];
export type TeamGroup = Schemas["GroupOut"];
export type Team = Schemas["TeamOut"];
export type OpenSlots = Schemas["OpenSlotsOut"];
export type Suggestion = Schemas["SuggestionOut"];
export type Discard = Schemas["DiscardOut"];
export type Presence = Schemas["PresenceOut"];
export type ConfirmedFact = Schemas["ConfirmedFactOut"];
export type GeneratedPokemon = Schemas["PokemonOut"];
export type Rule = Schemas["RuleOut"];
