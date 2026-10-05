/**
 * Routes of the application (docs/02-ddt/plan-web.md, "Pantallas"). The screens of the later
 * phases answer with `PendingPage` until they exist.
 */
import { Route, Routes } from "react-router";

import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";
import PendingPage from "./pages/PendingPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="pokemon/*" element={<PendingPage title="Catálogo" />} />
        <Route path="favoritos" element={<PendingPage title="Favoritos" />} />
        <Route path="reglas" element={<PendingPage title="Reglas" />} />
        <Route path="juego/*" element={<PendingPage title="Nuevo juego" />} />
        <Route path="hall-of-fame" element={<PendingPage title="Hall of Fame" />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
