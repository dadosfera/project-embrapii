import { useEffect, useRef, useState } from "react";

/**
 * Estado e efeitos comuns aos seletores com autocomplete (CatmatPicker, FornecedorPicker):
 * texto exibido, se o usuário está editando, se a lista está aberta, debounce da busca,
 * guarda contra resposta desatualizada (stale request) e fechar ao clicar fora.
 *
 * Cada seletor mantém seu próprio markup/linhas — este hook só cobre o "motor" comum.
 */

export const ESPERA_PADRAO_MS = 250;
export const MINIMO_PADRAO = 2;

export interface OpcoesAutocomplete<T> {
  /** Texto a mostrar quando o usuário não está editando (normalmente o nome do valor selecionado). */
  valorTexto: string;
  /** Busca no backend; recebe o termo já com trim. */
  buscar: (termo: string) => Promise<T>;
  /** Valor "sem resultado" (ex.: `[]`), usado ao limpar ou abortar a busca. */
  vazio: T;
  /** Mensagem mostrada quando `buscar` rejeita sem `Error` com mensagem própria. */
  mensagemErro: string;
  /** Mínimo de caracteres (após trim) para disparar a busca. */
  minimo?: number;
  /** Debounce em ms antes de chamar `buscar`. */
  esperaMs?: number;
}

export function useAutocomplete<T>({
  valorTexto,
  buscar,
  vazio,
  mensagemErro,
  minimo = MINIMO_PADRAO,
  esperaMs = ESPERA_PADRAO_MS,
}: OpcoesAutocomplete<T>) {
  const [texto, setTexto] = useState(valorTexto);
  const [editando, setEditando] = useState(false);
  const [aberto, setAberto] = useState(false);
  const [itens, setItens] = useState<T>(vazio);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const pedido = useRef(0);
  const raiz = useRef<HTMLDivElement>(null);

  // Seleção vinda de fora (URL, outra página): mostra o nome enquanto o usuário não estiver digitando.
  useEffect(() => {
    if (!editando) setTexto(valorTexto);
  }, [valorTexto, editando]);

  useEffect(() => {
    const termo = texto.trim();
    if (!editando || termo.length < minimo) {
      setItens(vazio);
      setCarregando(false);
      return;
    }
    const meu = ++pedido.current;
    setCarregando(true);
    const timer = window.setTimeout(() => {
      buscar(termo)
        .then((r) => {
          if (meu !== pedido.current) return;
          setItens(r);
          setErro(null);
        })
        .catch((e: unknown) => {
          if (meu !== pedido.current) return;
          setItens(vazio);
          setErro(e instanceof Error ? e.message : mensagemErro);
        })
        .finally(() => {
          if (meu === pedido.current) setCarregando(false);
        });
    }, esperaMs);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- buscar/vazio/mensagemErro/minimo/esperaMs
    // são estáveis por instância do hook (função importada e literais do chamador); só texto/editando
    // devem redisparar a busca.
  }, [texto, editando]);

  useEffect(() => {
    function fora(event: MouseEvent) {
      if (raiz.current && !raiz.current.contains(event.target as Node)) fechar();
    }
    document.addEventListener("mousedown", fora);
    return () => document.removeEventListener("mousedown", fora);
  });

  function fechar() {
    setAberto(false);
    setEditando(false);
  }

  /** onChange do campo: atualiza o texto e garante a lista aberta em modo de edição. */
  function aoDigitar(valor: string) {
    setTexto(valor);
    setEditando(true);
    setAberto(true);
  }

  /** Escape: fecha a lista e restaura o texto do valor selecionado (ou vazio, se não houver). */
  function aoEscapar() {
    fechar();
    setTexto(valorTexto);
  }

  return {
    raiz,
    texto,
    termo: texto.trim(),
    editando,
    aberto,
    itens,
    carregando,
    erro,
    minimo,
    setAberto,
    setTexto,
    aoDigitar,
    aoEscapar,
    fechar,
  };
}
