import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import { Link, Route, Routes, useLocation } from "react-router";

import { AppShell } from "./ui/AppShell";
import { ChunkCarregado, ChunkErrorBoundary } from "./ui/ChunkErrorBoundary";
import { EmptyState } from "./ui/EmptyState";
import { carregadoresDeRota, preCarregarTodasAsRotas } from "./rotas";

const Home = lazy(() => carregadoresDeRota["/"]().then((m) => ({ default: m.Home })));
const Medicamentos = lazy(() => carregadoresDeRota["/medicamentos"]().then((m) => ({ default: m.Medicamentos })));
const Compras = lazy(() => carregadoresDeRota["/compras"]().then((m) => ({ default: m.Compras })));
const Leitos = lazy(() => carregadoresDeRota["/leitos"]().then((m) => ({ default: m.Leitos })));
const Mapa = lazy(() => carregadoresDeRota["/mapa"]().then((m) => ({ default: m.Mapa })));
const Fornecedores = lazy(() => carregadoresDeRota["/fornecedores"]().then((m) => ({ default: m.Fornecedores })));

// Sem chunk próprio (fica no chunk de entrada, como o FalhaAoCarregar): página curta, sem tabela/gráfico.
function PaginaNaoEncontrada() {
  return (
    <main id="conteudo" tabIndex={-1} className="mx-auto max-w-[1440px] px-4 py-8 md:px-8">
      <EmptyState
        title="Página não encontrada"
        cause="O endereço acessado não existe neste painel."
        action={
          <Link
            to="/"
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]"
          >
            Ir para o Início
          </Link>
        }
      />
    </main>
  );
}

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

// Roda o import() de todas as rotas depois do primeiro paint, em ocioso, para o clique em
// qualquer link do menu já encontrar o chunk (ou boa parte dele) na memória do navegador.
function usarPreCargaEmOcioso() {
  useEffect(() => {
    const scheduler =
      typeof window.requestIdleCallback === "function"
        ? window.requestIdleCallback.bind(window)
        : (cb: () => void) => window.setTimeout(cb, 200);
    const cancelar =
      typeof window.cancelIdleCallback === "function" ? window.cancelIdleCallback.bind(window) : window.clearTimeout;
    const id = scheduler(preCarregarTodasAsRotas);
    return () => cancelar(id as never);
  }, []);
}

/**
 * Indicador de navegação pendente independente do Suspense: o BrowserRouter atualiza a
 * localização dentro de um `startTransition` (react-router 7), e o React 19 mantém a página
 * antiga visível enquanto a rota nova está pendente — o <Suspense fallback> só apareceria se
 * o chunk ainda não tivesse sido baixado quando a transição finalmente comitar. `marcarPendente`
 * é um `setState` comum (fora da transition do router), então ele têm prioridade e aparece de
 * imediato; o efeito abaixo limpa a marca assim que `pathname` alcança o destino pedido.
 */
function usarNavegacaoPendente(pathnameAtual: string) {
  const [destino, setDestino] = useState<string | null>(null);

  const marcarPendente = useCallback(
    (para: string) => {
      setDestino((atual) => (para === pathnameAtual ? atual : para));
    },
    [pathnameAtual],
  );

  useEffect(() => {
    if (destino !== null && destino === pathnameAtual) setDestino(null);
  }, [destino, pathnameAtual]);

  return { pendente: destino !== null, marcarPendente };
}

export default function App() {
  const { pathname } = useLocation();
  usarPreCargaEmOcioso();
  const { pendente, marcarPendente } = usarNavegacaoPendente(pathname);

  return (
    <AppShell pendente={pendente} aoNavegar={marcarPendente}>
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
            <Route path="*" element={<PaginaNaoEncontrada />} />
          </Routes>
          <ChunkCarregado />
        </Suspense>
      </ChunkErrorBoundary>
    </AppShell>
  );
}
