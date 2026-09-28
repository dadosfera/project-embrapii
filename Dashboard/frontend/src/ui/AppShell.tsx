import { type ReactNode, useState } from "react";
import { NavLink } from "react-router";

import { AutodriveChat } from "@/components/AutodriveChat";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { assetUrl } from "@/lib/base";
import { Icon } from "./Icon";
import type { IconName } from "./icons";

const DESTINOS: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: "/", label: "Início", icon: "home", end: true },
  { to: "/medicamentos", label: "Medicamentos", icon: "droplet" },
  { to: "/compras", label: "Compras", icon: "cart" },
  { to: "/leitos", label: "Leitos", icon: "activity" },
  { to: "/mapa", label: "Mapa", icon: "map" },
  { to: "/fornecedores", label: "Fornecedores", icon: "briefcase" },
];

function linkClass({ isActive }: { isActive: boolean }) {
  return [
    "inline-flex min-h-10 items-center gap-2 rounded-[var(--radius-sm)] px-3 text-sm font-semibold transition-colors",
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]",
    isActive ? "bg-primary-soft text-primary" : "text-muted hover:bg-subtle hover:text-[var(--text)]",
  ].join(" ");
}

function Navegacao({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      {DESTINOS.map((d) => (
        <NavLink key={d.to} to={d.to} end={d.end} className={linkClass} onClick={onNavigate}>
          <Icon name={d.icon} size={18} />
          {d.label}
        </NavLink>
      ))}
    </>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [aberto, setAberto] = useState(false);
  return (
    <div className="min-h-screen bg-surface">
      <header className="sticky top-0 z-20 border-b border-line bg-panel/95 backdrop-blur">
        <div className="mx-auto flex min-h-16 max-w-[1440px] items-center gap-4 px-4 md:px-8">
          <NavLink to="/" className="flex items-center gap-3">
            <img src={assetUrl("logos/DF-LogoHRZ.svg")} alt="Dadosfera" className="h-7 w-auto" />
            <span className="hidden border-l border-line pl-3 text-xs font-semibold text-muted sm:inline">
              Projeto EMBRAPII · DCC/UFMG
            </span>
          </NavLink>

          <nav aria-label="Navegação principal" className="ml-auto hidden items-center gap-1 lg:flex">
            <Navegacao />
          </nav>

          <Sheet open={aberto} onOpenChange={setAberto}>
            <SheetTrigger
              className="ml-auto inline-flex h-10 w-10 items-center justify-center rounded-[var(--radius-sm)] text-[var(--text)] hover:bg-subtle lg:hidden"
              aria-label="Abrir menu"
            >
              <Icon name="menu" size={22} />
            </SheetTrigger>
            <SheetContent side="right" className="w-72 bg-panel p-4" aria-describedby={undefined}>
              <SheetTitle className="px-1 text-sm font-semibold text-muted">Navegação</SheetTitle>
              <nav aria-label="Navegação principal (menu)" className="mt-4 flex flex-col gap-1">
                <Navegacao onNavigate={() => setAberto(false)} />
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </header>
      {children}
      <AutodriveChat />
    </div>
  );
}
