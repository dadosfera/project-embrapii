import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
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

/**
 * true numa conexão explicitamente "Economia de dados" (Data Saver) ou 2G/muito lenta: pula o
 * pré-carregamento em massa (só o hover/foco no link, em Navegacao.tsx, continua pré-carregando
 * sob demanda). `navigator.connection` é Chromium-only; onde não existe, o pré-carregamento roda
 * normalmente.
 */
function devePularPreCargaPorConexao(): boolean {
  const conexao = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } })
    .connection;
  if (!conexao) return false;
  if (conexao.saveData) return true;
  return conexao.effectiveType === "2g" || conexao.effectiveType === "slow-2g";
}

// Roda o import() de todas as rotas depois do primeiro paint, em ocioso, para o clique em
// qualquer link do menu já encontrar o chunk (ou boa parte dele) na memória do navegador.
//
// Se o usuário estiver offline nesse momento, o import() falha e a promise rejeitada não fica
// cacheada pelo navegador (a rota simplesmente não pré-carregou) — não precisa de tratamento
// aqui: se uma navegação real mais tarde precisar desse chunk e ele ainda não existir/tiver sido
// trocado por um redeploy, cai no autoReload do ChunkErrorBoundary (App.tsx), que recarrega a
// página uma vez.
function usarPreCargaEmOcioso() {
  useEffect(() => {
    if (devePularPreCargaPorConexao()) return;
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

const TEMPO_LIMITE_PENDENCIA_MS = 15_000;

/**
 * Indicador de navegação pendente independente do Suspense: o BrowserRouter atualiza a
 * localização dentro de um `startTransition` (react-router 7), e o React 19 mantém a página
 * antiga visível enquanto a rota nova está pendente — o <Suspense fallback> só apareceria se
 * o chunk ainda não tivesse sido baixado quando a transição finalmente comitar. `marcarPendente`
 * é um `setState` comum (fora da transition do router), então ele tem prioridade e aparece de
 * imediato.
 *
 * A pendência é limpa (a) por `resolver`, chamado por <RotaRevelada> quando o <Suspense> REALMENTE
 * revela uma rota nova — não confundir com `location.pathname`/`useLocation()`, que já muda assim
 * que o BrowserRouter aceita a navegação, ANTES do chunk da rota nova terminar de carregar (o
 * `startTransition` do router só segura o conteúdo do próprio <Suspense>, não o resto da árvore;
 * confirmado throttlando a rede e observando os dois momentos por logs). Limpar pelo location
 * mudaria a barra quase no mesmo instante em que ela aparece, na maioria das navegações — e (b)
 * por um timeout de segurança: se por algum motivo a rota nunca for revelada (chunk que nunca
 * chega, erro que o ChunkErrorBoundary trata sem autoReload), a barra não fica presa para sempre.
 */
function usarNavegacaoPendente(pathnameAtual: string) {
  const [pendente, setPendente] = useState(false);
  const timeoutRef = useRef<number | null>(null);

  const limparTimeout = useCallback(() => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const marcarPendente = useCallback(
    (destino: string) => {
      if (destino === pathnameAtual) return; // já está nessa rota: não houve navegação de fato
      setPendente(true);
      limparTimeout();
      timeoutRef.current = window.setTimeout(() => setPendente(false), TEMPO_LIMITE_PENDENCIA_MS);
    },
    [pathnameAtual, limparTimeout],
  );

  // Limpa em QUALQUER revelação de rota (não só a que foi clicada pelo menu): cobre Voltar/
  // Avançar do navegador, um <Link> fora do menu, ou o usuário mudar de ideia e clicar noutro
  // destino antes do primeiro terminar de carregar (só a última rota chega a ser revelada).
  const resolver = useCallback(() => {
    setPendente(false);
    limparTimeout();
  }, [limparTimeout]);

  useEffect(() => limparTimeout, [limparTimeout]);

  return { pendente, marcarPendente, resolver };
}

/**
 * Monta de novo toda vez que o `pathname` muda — mas, como só existe dentro do <Suspense>, o
 * remount (e o efeito de mount) só chega a comitar quando o conteúdo da rota nova realmente
 * aparece: se o chunk ainda estiver pendente, React segura esse remount junto com o resto do
 * conteúdo do <Suspense> (ver comentário de usarNavegacaoPendente). É esse atraso natural que
 * torna esse componente o sinal certo de "a rota revelou", diferente de `location.pathname`.
 */
function RotaRevelada({ aoRevelar }: { aoRevelar: () => void }) {
  useEffect(() => {
    aoRevelar();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- só quer rodar uma vez por remount
  }, []);
  return null;
}

export default function App() {
  const { pathname } = useLocation();
  usarPreCargaEmOcioso();
  const { pendente, marcarPendente, resolver } = usarNavegacaoPendente(pathname);

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
          <RotaRevelada key={pathname} aoRevelar={resolver} />
          <ChunkCarregado />
        </Suspense>
      </ChunkErrorBoundary>
    </AppShell>
  );
}
