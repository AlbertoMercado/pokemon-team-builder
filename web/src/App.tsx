/**
 * Routes of the application (docs/02-ddt/plan-web.md, "Pantallas"). The screens of the later
 * phases answer with `PendingPage` until they exist.
 */
import { Route, Routes } from "react-router";

import Layout from "./components/Layout";
import CatalogPage from "./pages/CatalogPage";
import FavoritesPage from "./pages/FavoritesPage";
import GamesPage from "./pages/GamesPage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";
import PendingPage from "./pages/PendingPage";
import PokemonPage from "./pages/PokemonPage";
import ReviewPage from "./pages/ReviewPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="pokemon" element={<CatalogPage />} />
        <Route path="pokemon/:pokemon" element={<PokemonPage />} />
        <Route path="favoritos" element={<FavoritesPage />} />
        <Route path="reglas" element={<PendingPage title="Reglas" />} />
        <Route path="juego" element={<GamesPage />} />
        <Route path="juego/:game/revision" element={<ReviewPage />} />
        <Route path="juego/:game/resultado" element={<PendingPage title="Resultado" />} />
        <Route path="hall-of-fame" element={<PendingPage title="Hall of Fame" />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
