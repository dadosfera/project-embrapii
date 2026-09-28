import { Component, type ErrorInfo, type ReactNode, useEffect } from "react";

/**
 * Captura falhas de import dinâmico (chunk lazy). Depois de um redeploy, os chunks com hash antigo somem
 * e abas abertas recebem 404 ao navegar; sem boundary, o React desmonta tudo e a tela fica em branco.
 *
 * Com `autoReload`, a primeira falha de chunk recarrega a página uma vez (flag em sessionStorage, para
 * não entrar em laço). `<ChunkCarregado />`, renderizado dentro do Suspense, limpa a flag quando um chunk
 * carrega com sucesso.
 */

export const FLAG_RECARGA = "embrapii:chunk-reload";

const PADRAO_CHUNK =
  /Failed to fetch dynamically imported module|error loading dynamically imported module|Importing a module script failed|Loading (CSS )?chunk .* failed|ChunkLoadError|Unable to preload CSS/i;

export function ehErroDeChunk(erro: unknown): boolean {
  if (!(erro instanceof Error)) return false;
  return erro.name === "ChunkLoadError" || PADRAO_CHUNK.test(erro.message);
}

function lerFlag(): boolean {
  try {
    return sessionStorage.getItem(FLAG_RECARGA) === "1";
  } catch {
    return true; // sem storage não dá para proteger contra laço: não recarrega sozinho
  }
}

function gravarFlag(): void {
  try {
    sessionStorage.setItem(FLAG_RECARGA, "1");
  } catch {
    /* sem storage */
  }
}

/** Limpa a flag de recarga quando o conteúdo lazy terminou de carregar. */
export function ChunkCarregado() {
  useEffect(() => {
    try {
      sessionStorage.removeItem(FLAG_RECARGA);
    } catch {
      /* sem storage */
    }
  }, []);
  return null;
}

type Props = {
  children: ReactNode;
  /** `ehChunk` indica se o erro capturado é de import dinâmico (chunk) ou outro erro qualquer. */
  fallback: (recarregar: () => void, ehChunk: boolean) => ReactNode;
  /** Recarrega a página sozinho, uma vez, na primeira falha de chunk. */
  autoReload?: boolean;
  /** Muda a chave (ex.: pathname) para sair do estado de erro ao navegar. */
  resetKey?: unknown;
  /** Injetável para teste. */
  recarregar?: () => void;
};

type State = { erro: Error | null; recarregando: boolean };

export class ChunkErrorBoundary extends Component<Props, State> {
  state: State = { erro: null, recarregando: false };

  static getDerivedStateFromError(erro: Error): Partial<State> {
    return { erro };
  }

  componentDidCatch(erro: Error, info: ErrorInfo) {
    if (this.props.autoReload && ehErroDeChunk(erro) && !lerFlag()) {
      gravarFlag();
      this.setState({ recarregando: true });
      this.recarregar();
      return;
    }
    console.warn("Falha ao carregar parte da interface", erro, info.componentStack);
  }

  componentDidUpdate(anterior: Props) {
    if (this.state.erro && anterior.resetKey !== this.props.resetKey) {
      this.setState({ erro: null, recarregando: false });
    }
  }

  recarregar = () => {
    (this.props.recarregar ?? (() => window.location.reload()))();
  };

  render() {
    if (this.state.recarregando) return null;
    if (this.state.erro) return this.props.fallback(this.recarregar, ehErroDeChunk(this.state.erro));
    return this.props.children;
  }
}
