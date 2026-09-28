import { lazy, Suspense } from "react";
import { Route, Routes, useLocation } from "react-router";

import { AppShell } from "./ui/AppShell";
import { ChunkCarregado, ChunkErrorBoundary } from "./ui/ChunkErrorBoundary";
import { EmptyState } from "./ui/EmptyState";

const Home = lazy(() => import("./pages/Home").then((m) => ({ default: m.Home })));
const Medicamentos = lazy(() => import("./pages/Medicamentos").then((m) => ({ default: m.Medicamentos })));
const Compras = lazy(() => import("./pages/Compras").then((m) => ({ default: m.Compras })));
const Leitos = lazy(() => import("./pages/Leitos").then((m) => ({ default: m.Leitos })));
const Mapa = lazy(() => import("./pages/Mapa").then((m) => ({ default: m.Mapa })));
const Fornecedores = lazy(() => import("./pages/Fornecedores").then((m) => ({ default: m.Fornecedores })));

// É o <main> da página enquanto o chunk carrega, para o link "Pular para o conteúdo" ter alvo.
function Carregando() {
  return (
    <main id="conteudo" tabIndex={-1} className="mx-auto max-w-[1440px] px-4 py-8 md:px-8">
      <div role="status" aria-busy="true" aria-label="Carregando página" className="space-y-4">
        {/* Mesmo visual do <Skeleton>, sem cn()/tailwind-merge no chunk de entrada. */}
        <div className="h-10 w-72 animate-pulse rounded-md bg-subtle" />
        <div className="h-32 w-full animate-pulse rounded-md bg-subtle" />
        <div className="h-64 w-full animate-pulse rounded-md bg-subtle" />
      </div>
    </main>
  );
}

// Sem <Button> (cn/tailwind-merge) de propósito: este fallback fica no chunk de entrada.
function FalhaAoCarregar({ recarregar, ehChunk }: { recarregar: () => void; ehChunk: boolean }) {
  return (
    <main id="conteudo" tabIndex={-1} className="mx-auto max-w-[1440px] px-4 py-8 md:px-8">
      <EmptyState
        title="Não foi possível carregar a página"
        cause={
          ehChunk
            ? "O painel pode ter sido atualizado enquanto esta aba estava aberta. Recarregue para buscar a versão nova."
            : "Ocorreu um erro inesperado ao exibir esta página."
        }
        action={
          <button
            type="button"
            onClick={recarregar}
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]"
          >
            Recarregar
          </button>
        }
      />
    </main>
  );
}

export default function App() {
  const { pathname } = useLocation();
  return (
    <AppShell>
      <ChunkErrorBoundary
        autoReload
        resetKey={pathname}
        fallback={(recarregar, ehChunk) => <FalhaAoCarregar recarregar={recarregar} ehChunk={ehChunk} />}
      >
        <Suspense fallback={<Carregando />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/medicamentos" element={<Medicamentos />} />
            <Route path="/compras" element={<Compras />} />
            <Route path="/leitos" element={<Leitos />} />
            <Route path="/mapa" element={<Mapa />} />
            <Route path="/fornecedores" element={<Fornecedores />} />
          </Routes>
          <ChunkCarregado />
        </Suspense>
      </ChunkErrorBoundary>
    </AppShell>
  );
}
