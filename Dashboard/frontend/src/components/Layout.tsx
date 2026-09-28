import { type ReactNode } from "react";
import { NavLink } from "react-router";

import { assetUrl } from "../lib/base";
import { AutodriveChat } from "./AutodriveChat";

type LayoutProps = {
  children: ReactNode;
};

function navClass({ isActive }: { isActive: boolean }) {
  return [
    "nav-link shrink-0 px-3 py-2 text-sm font-medium",
    isActive ? "nav-link-active" : "",
  ].join(" ");
}

export function Layout({ children }: LayoutProps) {
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
              src={assetUrl("logos/logodadosfera.png")}
              alt=""
              className="brand-logo"
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
        </div>
      </header>

      {children}

      <AutodriveChat />
    </div>
  );
}
