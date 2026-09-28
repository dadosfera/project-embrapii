import { lazy, type ReactNode, Suspense, useRef, useState } from "react";
import { NavLink } from "react-router";

import { AutodriveChat } from "@/components/AutodriveChat";
import { assetUrl } from "@/lib/base";
import { Icon } from "./Icon";
import { Navegacao } from "./Navegacao";

// O menu mobile (Radix Dialog + focus scope + remove-scroll) só é baixado no primeiro toque no botão.
const MobileMenu = lazy(() => import("./MobileMenu").then((m) => ({ default: m.MobileMenu })));

export function AppShell({ children }: { children: ReactNode }) {
  const [aberto, setAberto] = useState(false);
  const [menuMontado, setMenuMontado] = useState(false);
  const botaoMenu = useRef<HTMLButtonElement>(null);

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

          <button
            ref={botaoMenu}
            type="button"
            className="ml-auto inline-flex h-10 w-10 items-center justify-center rounded-[var(--radius-sm)] text-[var(--text)] hover:bg-subtle lg:hidden"
            aria-label="Abrir menu"
            aria-haspopup="dialog"
            aria-expanded={aberto}
            aria-controls={aberto ? "menu-mobile" : undefined}
            onClick={() => {
              setMenuMontado(true);
              setAberto(true);
            }}
          >
            <Icon name="menu" size={22} />
          </button>
          {menuMontado && (
            <Suspense fallback={null}>
              <MobileMenu open={aberto} onOpenChange={setAberto} triggerRef={botaoMenu} />
            </Suspense>
          )}
        </div>
      </header>
      {children}
      <AutodriveChat />
    </div>
  );
}
