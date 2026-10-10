/** Routes of the application (docs/02-ddt/web.md, "Pantallas"). */
import { Route, Routes } from "react-router";

import Layout from "./components/Layout";
import CatalogPage from "./pages/CatalogPage";
import FavoritesPage from "./pages/FavoritesPage";
import GamesPage from "./pages/GamesPage";
import HallOfFamePage from "./pages/HallOfFamePage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";
import PokedexDetailPage from "./pages/PokedexDetailPage";
import PokedexGamePage from "./pages/PokedexGamePage";
import PokedexListPage from "./pages/PokedexListPage";
import PokedexPokemonPage from "./pages/PokedexPokemonPage";
import PokemonPage from "./pages/PokemonPage";
import ResultPage from "./pages/ResultPage";
import RulesPage from "./pages/RulesPage";
import ReviewPage from "./pages/ReviewPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="pokemon" element={<CatalogPage />} />
        <Route path="pokemon/:pokemon" element={<PokemonPage />} />
        <Route path="favoritos" element={<FavoritesPage />} />
        <Route path="reglas" element={<RulesPage />} />
        <Route path="juego" element={<GamesPage />} />
        <Route path="juego/:game/revision" element={<ReviewPage />} />
        <Route path="juego/:game/resultado" element={<ResultPage />} />
        <Route path="hall-of-fame" element={<HallOfFamePage />} />
        <Route path="pokedex" element={<PokedexListPage />} />
        <Route path="pokedex/:game" element={<PokedexGamePage />} />
        <Route path="pokedex/:game/detalle" element={<PokedexDetailPage />} />
        <Route path="pokedex/:game/pokemon/:species" element={<PokedexPokemonPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
