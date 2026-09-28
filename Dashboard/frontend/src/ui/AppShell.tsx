import { lazy, type ReactNode, Suspense, useEffect, useRef, useState } from "react";
import { NavLink, useLocation } from "react-router";

import { AutodriveChat } from "@/components/AutodriveChat";
import { assetUrl } from "@/lib/base";
import { ChunkErrorBoundary } from "./ChunkErrorBoundary";
import { Icon } from "./Icon";
import { Navegacao } from "./Navegacao";

// O menu mobile (Radix Dialog + focus scope + remove-scroll) fica fora da entrada. O chunk é pré-carregado
// quando o ponteiro/foco chega no botão e montado no primeiro toque. O import() é memoizado pelo navegador.
const carregarMenu = () => import("./MobileMenu");
const MobileMenu = lazy(() => carregarMenu().then((m) => ({ default: m.MobileMenu })));
const preCarregarMenu = () => {
  carregarMenu().catch(() => {
    /* a falha real aparece (e é tratada) quando o lazy montar */
  });
};

// Se o chunk do menu não carregar, mostra a navegação num painel simples, sem Dialog.
function MenuSimples({ onNavigate }: { onNavigate: () => void }) {
  return (
    <nav
      id="menu-mobile"
      aria-label="Navegação principal (menu)"
      className="absolute inset-x-0 top-full flex flex-col gap-1 border-b border-line bg-panel p-4 shadow-[var(--shadow-card)] lg:hidden"
    >
      <Navegacao onNavigate={onNavigate} />
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [aberto, setAberto] = useState(false);
  const [menuMontado, setMenuMontado] = useState(false);
  const botaoMenu = useRef<HTMLButtonElement>(null);
  const { pathname } = useLocation();

  // Fecha o menu em qualquer troca de rota (link do menu, voltar do navegador, link na página).
  useEffect(() => setAberto(false), [pathname]);

  return (
    <div className="min-h-screen bg-surface">
      {/* Primeiro foco da página. Cada página renderiza seu <main id="conteudo" tabIndex={-1}>. */}
      <a
        href="#conteudo"
        onClick={(e) => {
          // Com <base href> (prefixo do Orchest), "#conteudo" resolveria para outra URL; foca direto.
          e.preventDefault();
          document.getElementById("conteudo")?.focus();
        }}
        className="sr-only z-50 rounded-[var(--radius-sm)] bg-panel px-4 py-2 text-sm font-semibold text-primary shadow-[var(--shadow-card)] focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]"
      >
        Pular para o conteúdo
      </a>
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
            aria-controls={menuMontado && aberto ? "menu-mobile" : undefined}
            onPointerEnter={preCarregarMenu}
            onFocus={preCarregarMenu}
            onTouchStart={preCarregarMenu}
            onClick={() => {
              setMenuMontado(true);
              setAberto(true);
            }}
          >
            <Icon name="menu" size={22} />
          </button>
          {menuMontado && (
            <ChunkErrorBoundary
              fallback={() => (aberto ? <MenuSimples onNavigate={() => setAberto(false)} /> : null)}
            >
              <Suspense fallback={null}>
                <MobileMenu open={aberto} onOpenChange={setAberto} triggerRef={botaoMenu} />
              </Suspense>
            </ChunkErrorBoundary>
          )}
        </div>
      </header>
      {children}
      <AutodriveChat />
    </div>
  );
}
