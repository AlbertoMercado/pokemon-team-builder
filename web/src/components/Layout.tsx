/**
 * The frame of every screen: navigation bar, notice when the API is unavailable, content and the
 * notice of the images and the data.
 */
import { Link, NavLink, Outlet } from "react-router";

import ApiStatusBanner from "./ApiStatusBanner";
import ImageNotice from "./ImageNotice";

const SECTIONS = [
  { to: "/pokemon", label: "Catálogo" },
  { to: "/favoritos", label: "Favoritos" },
  { to: "/reglas", label: "Reglas" },
  { to: "/juego", label: "Nuevo juego" },
  { to: "/hall-of-fame", label: "Hall of Fame" },
  { to: "/pokedex", label: "Pokédex" },
] as const;

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <Link to="/" className="font-bold text-red-700">
            pokemon-team-builder
          </Link>
          <nav aria-label="Principal">
            <ul className="flex flex-wrap gap-x-4 gap-y-1">
              {SECTIONS.map(({ to, label }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    className={({ isActive }) =>
                      isActive
                        ? "font-semibold text-red-700 underline underline-offset-4"
                        : "text-slate-700 hover:text-red-700"
                    }
                  >
                    {label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>
      <ApiStatusBanner />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
        <Outlet />
      </main>
      <ImageNotice />
    </div>
  );
}
