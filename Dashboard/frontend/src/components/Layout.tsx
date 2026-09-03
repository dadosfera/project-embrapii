import { type ReactNode, useState } from "react";
import { NavLink } from "react-router";

import {
  getThemePreference,
  setThemePreference,
  type ThemePreference,
} from "../theme";

type LayoutProps = {
  children: ReactNode;
};

function navClass({ isActive }: { isActive: boolean }) {
  return [
    "nav-link shrink-0 px-3 py-2 text-sm font-medium",
    isActive ? "nav-link-active" : "",
  ].join(" ");
}

const themeMeta: Record<ThemePreference, { icon: string; label: string }> = {
  system: { icon: "◐", label: "Tema do sistema" },
  light: { icon: "☀", label: "Tema claro" },
  dark: { icon: "☾", label: "Tema escuro" },
};

export function Layout({ children }: LayoutProps) {
  const [theme, setTheme] = useState<ThemePreference>(getThemePreference);

  function cycleTheme() {
    const next: Record<ThemePreference, ThemePreference> = {
      system: "light",
      light: "dark",
      dark: "system",
    };
    const nextTheme = next[theme];
    setTheme(nextTheme);
    setThemePreference(nextTheme);
  }

  return (
    <div className="app-shell">
      <header className="app-header sticky top-0 z-20 border-b backdrop-blur-xl">
        <div className="mx-auto grid min-h-16 max-w-[1440px] grid-cols-[1fr_auto] items-center gap-x-3 px-4 md:grid-cols-[auto_1fr_auto] md:px-8">
          <NavLink
            to="/"
            className="brand-mark"
            aria-label="Dadosfera — Início"
          >
            <img
              src="/logos/logodadosfera.png"
              alt=""
              className="brand-logo brand-logo-light"
              aria-hidden="true"
            />
            <img
              src="/logos/dadosferabranco.png"
              alt=""
              className="brand-logo brand-logo-dark"
              aria-hidden="true"
            />
          </NavLink>

          <nav
            aria-label="Navegação principal"
            className="scrollbar-none col-span-2 row-start-2 flex max-w-full items-center gap-1 overflow-x-auto py-2 md:col-span-1 md:col-start-2 md:row-start-1 md:justify-center"
          >
            <NavLink to="/" end className={navClass}>
              Início
            </NavLink>

            <NavLink
              to="/medicamentos"
              className={navClass}
            >
              Medicamentos
            </NavLink>

            <NavLink
              to="/compras"
              className={navClass}
            >
              Compras
            </NavLink>

            <NavLink
              to="/leitos"
              className={navClass}
            >
              Leitos
            </NavLink>

            <NavLink
              to="/mapa"
              className={navClass}
            >
              Mapa
            </NavLink>
            <NavLink
              to="/fornecedores"
              className={navClass}
            >
              Fornecedores
            </NavLink>
          </nav>

          <button
            type="button"
            className="theme-toggle"
            onClick={cycleTheme}
            aria-label={`${themeMeta[theme].label}. Alterar tema.`}
            title={themeMeta[theme].label}
          >
            <span aria-hidden="true">{themeMeta[theme].icon}</span>
          </button>
        </div>
      </header>

      {children}
    </div>
  );
}
