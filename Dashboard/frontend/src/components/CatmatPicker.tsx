import { useEffect, useId, useRef, useState } from "react";
import { Command as CommandPrimitive } from "cmdk";

import { buscarCatmatAgrupado, type BlocoBuscaCatmat, type GrupoCatmat } from "../lib/api";
import { cn } from "../lib/utils";
import { Icon } from "../ui/Icon";

/**
 * Seletor único de medicamento CATMAT (Medicamentos, Mapa e Compras).
 *
 * Um campo com autocomplete: busca sem acento no backend (/busca-agrupada), resultados agrupados por composição
 * (princípio ativo), cada linha é um item-base com as variantes somadas e selos de onde há dado. Escolher já
 * seleciona — sem "Buscar" nem "Pesquisar".
 */

const ESPERA_MS = 250;
const MINIMO = 2;

export function SelosDados({
  temCompras,
  temEstoque,
  className,
}: {
  temCompras: boolean;
  temEstoque: boolean | null;
  className?: string;
}) {
  const semDados = !temCompras && temEstoque === false;
  return (
    <span className={cn("flex shrink-0 flex-wrap gap-1", className)}>
      {temCompras && <Selo tom="primario">compras</Selo>}
      {temEstoque && <Selo tom="sucesso">estoque</Selo>}
      {semDados && <Selo tom="neutro">sem dados</Selo>}
    </span>
  );
}

function Selo({ tom, children }: { tom: "primario" | "sucesso" | "neutro"; children: string }) {
  const cores = {
    primario: "bg-primary-soft text-primary",
    sucesso: "bg-[var(--success-soft)] text-[var(--text)]",
    neutro: "bg-subtle text-muted",
  }[tom];
  return <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-medium leading-4", cores)}>{children}</span>;
}

type Props = {
  id: string;
  label: string;
  value: GrupoCatmat | null;
  onSelect: (grupo: GrupoCatmat | null) => void;
  placeholder?: string;
  className?: string;
};

export function CatmatPicker({ id, label, value, onSelect, placeholder, className }: Props) {
  const listaId = useId();
  const [texto, setTexto] = useState(value?.nome ?? "");
  const [editando, setEditando] = useState(false);
  const [aberto, setAberto] = useState(false);
  const [blocos, setBlocos] = useState<BlocoBuscaCatmat[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const pedido = useRef(0);
  const raiz = useRef<HTMLDivElement>(null);

  // Seleção vinda de fora (URL, outra página): mostra o nome enquanto o usuário não estiver digitando.
  useEffect(() => {
    if (!editando) setTexto(value?.nome ?? "");
  }, [value, editando]);

  useEffect(() => {
    const termo = texto.trim();
    if (!editando || termo.length < MINIMO) {
      setBlocos([]);
      setCarregando(false);
      return;
    }
    const meu = ++pedido.current;
    setCarregando(true);
    const timer = window.setTimeout(() => {
      buscarCatmatAgrupado(termo)
        .then((r) => {
          if (meu !== pedido.current) return;
          setBlocos(r);
          setErro(null);
        })
        .catch((e: unknown) => {
          if (meu !== pedido.current) return;
          setBlocos([]);
          setErro(e instanceof Error ? e.message : "Não foi possível consultar o catálogo.");
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

  function escolher(grupo: GrupoCatmat) {
    onSelect(grupo);
    setTexto(grupo.nome);
    fechar();
  }

  const total = blocos.reduce((n, b) => n + b.itens.length, 0);
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
            // o contêiner já mostra o foco; o :focus-visible global (fora de @layer) desenharia um segundo contorno
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
            placeholder={placeholder ?? "Digite o nome ou o código CATMAT (ex.: dipirona, BR0267203)"}
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
              aria-label="Limpar medicamento"
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
            {!erro && !carregando && total === 0 && (
              <CommandPrimitive.Empty className="px-3 py-4 text-sm text-muted">
                Nenhum medicamento com “{termo}”. Tente o princípio ativo sem a dose ou o código CATMAT.
              </CommandPrimitive.Empty>
            )}
            {blocos.map((bloco) => (
              <CommandPrimitive.Group
                key={bloco.composicao}
                heading={bloco.composicao}
                className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:pb-1 [&_[cmdk-group-heading]]:pt-2 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wide [&_[cmdk-group-heading]]:text-muted"
              >
                {bloco.itens.map((g) => (
                  <CommandPrimitive.Item
                    key={g.base}
                    value={g.base}
                    onSelect={() => escolher(g)}
                    className="flex cursor-pointer items-start gap-3 rounded-[var(--radius-sm)] px-2 py-2 text-sm data-[selected=true]:bg-primary-tint"
                  >
                    <span className="min-w-0 flex-1">
                      <span className="line-clamp-2 text-[var(--text)]">{g.nome}</span>
                      <span className="mt-0.5 block text-xs text-muted">
                        {g.base}
                        {g.variantes.length > 1 ? ` · ${g.variantes.length} códigos reunidos` : ""}
                      </span>
                    </span>
                    <SelosDados temCompras={g.tem_compras} temEstoque={g.tem_estoque} className="pt-0.5" />
                  </CommandPrimitive.Item>
                ))}
              </CommandPrimitive.Group>
            ))}
          </CommandPrimitive.List>
        )}
      </CommandPrimitive>
    </div>
  );
}
