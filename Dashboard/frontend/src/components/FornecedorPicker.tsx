import { useEffect, useId, useRef, useState } from "react";
import { Command as CommandPrimitive } from "cmdk";

import { buscarFornecedoresAutocomplete, type FornecedorAutocomplete } from "../lib/api";
import { cn } from "../lib/utils";
import { Icon } from "../ui/Icon";
import { formatarCnpj, moedaCompacta } from "../ui/format";

/**
 * Seletor de fornecedor com autocomplete (Compras e Fornecedores), no mesmo padrão do
 * CatmatPicker: campo único, busca sem acento no backend (/api/fornecedores/busca),
 * debounce, mínimo de caracteres e guarda contra resposta desatualizada.
 */

const ESPERA_MS = 250;
const MINIMO = 2;

type Props = {
  id: string;
  label: string;
  value: FornecedorAutocomplete | null;
  onSelect: (fornecedor: FornecedorAutocomplete | null) => void;
  placeholder?: string;
  className?: string;
};

export function FornecedorPicker({ id, label, value, onSelect, placeholder, className }: Props) {
  const listaId = useId();
  const [texto, setTexto] = useState(value?.nome ?? "");
  const [editando, setEditando] = useState(false);
  const [aberto, setAberto] = useState(false);
  const [itens, setItens] = useState<FornecedorAutocomplete[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const pedido = useRef(0);
  const raiz = useRef<HTMLDivElement>(null);

  // Seleção vinda de fora: mostra o nome enquanto o usuário não estiver digitando.
  useEffect(() => {
    if (!editando) setTexto(value?.nome ?? "");
  }, [value, editando]);

  useEffect(() => {
    const termo = texto.trim();
    if (!editando || termo.length < MINIMO) {
      setItens([]);
      setCarregando(false);
      return;
    }
    const meu = ++pedido.current;
    setCarregando(true);
    const timer = window.setTimeout(() => {
      buscarFornecedoresAutocomplete(termo)
        .then((r) => {
          if (meu !== pedido.current) return;
          setItens(r);
          setErro(null);
        })
        .catch((e: unknown) => {
          if (meu !== pedido.current) return;
          setItens([]);
          setErro(e instanceof Error ? e.message : "Não foi possível consultar os fornecedores.");
        })
        .finally(() => {
          if (meu === pedido.current) setCarregando(false);
        });
    }, ESPERA_MS);
    return () => window.clearTimeout(timer);
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

  function escolher(fornecedor: FornecedorAutocomplete) {
    onSelect(fornecedor);
    setTexto(fornecedor.nome);
    fechar();
  }

  const termo = texto.trim();
  const mostrarLista = aberto && editando && termo.length >= MINIMO;

  return (
    <div ref={raiz} className={cn("relative", className)}>
      <label htmlFor={id} className="block text-sm font-semibold text-[var(--text)]">
        {label}
      </label>

      <CommandPrimitive shouldFilter={false} loop className="mt-2">
        <div className="flex h-10 items-center gap-2 rounded-[var(--radius-md)] border border-line bg-panel px-3 shadow-xs transition-[color,box-shadow] focus-within:border-ring focus-within:ring-[3px] focus-within:ring-ring/50">
          <Icon name="search" size={16} className="text-muted" />
          {/* <input> comum (não o do cmdk, que troca o id): setas e Enter seguem com o cmdk pelo keydown da raiz. */}
          <input
            id={id}
            type="text"
            role="combobox"
            autoComplete="off"
            aria-autocomplete="list"
            style={{ outline: "none" }}
            value={texto}
            onChange={(event) => {
              setTexto(event.target.value);
              setEditando(true);
              setAberto(true);
            }}
            onFocus={(event) => {
              setAberto(true);
              if (value) event.currentTarget.select();
            }}
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                fechar();
                setTexto(value?.nome ?? "");
              }
            }}
            placeholder={placeholder ?? "Digite o nome ou o CNPJ do fornecedor"}
            aria-controls={listaId}
            aria-expanded={mostrarLista}
            className="h-full min-w-0 flex-1 bg-transparent text-sm text-[var(--text)] outline-hidden placeholder:text-muted"
          />
          {carregando && <span className="text-xs text-muted" aria-live="polite">buscando…</span>}
          {value && !editando && (
            <button
              type="button"
              onClick={() => {
                onSelect(null);
                setTexto("");
              }}
              aria-label="Limpar fornecedor"
              className="rounded-[var(--radius-sm)] p-1 text-muted hover:bg-subtle hover:text-[var(--text)]"
            >
              <Icon name="close" size={16} />
            </button>
          )}
        </div>

        {mostrarLista && (
          <CommandPrimitive.List
            id={listaId}
            className="absolute inset-x-0 top-full z-30 mt-1 max-h-[min(440px,60vh)] overflow-y-auto rounded-[var(--radius-md)] border border-line bg-panel p-1 shadow-lg"
          >
            {erro && <div className="px-3 py-4 text-sm text-[var(--danger-text)]">{erro}</div>}
            {!erro && !carregando && itens.length === 0 && (
              <CommandPrimitive.Empty className="px-3 py-4 text-sm text-muted">
                Nenhum fornecedor com “{termo}”.
              </CommandPrimitive.Empty>
            )}
            {itens.map((f) => (
              <CommandPrimitive.Item
                key={f.fornecedor_id}
                value={String(f.fornecedor_id)}
                onSelect={() => escolher(f)}
                className="flex cursor-pointer items-start gap-3 rounded-[var(--radius-sm)] px-2 py-2 text-sm data-[selected=true]:bg-primary-tint"
              >
                <span className="min-w-0 flex-1">
                  <span className="line-clamp-2 text-[var(--text)]">{f.nome}</span>
                  <span className="mt-0.5 block text-xs text-muted">{formatarCnpj(f.cnpj)}</span>
                </span>
                <span className="shrink-0 whitespace-nowrap text-right text-xs text-muted">
                  <span className="block font-medium text-[var(--text)]">{moedaCompacta(f.valor_total)}</span>
                  <span className="block">
                    {f.numero_compras} {f.numero_compras === 1 ? "compra" : "compras"}
                  </span>
                </span>
              </CommandPrimitive.Item>
            ))}
          </CommandPrimitive.List>
        )}
      </CommandPrimitive>
    </div>
  );
}
