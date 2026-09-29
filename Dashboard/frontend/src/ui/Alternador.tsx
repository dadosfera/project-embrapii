import type { KeyboardEvent } from "react";
import { cn } from "@/lib/utils";

type Opcao<T extends string> = { valor: T; rotulo: string };

type Props<T extends string> = {
  rotulo: string;
  opcoes: Opcao<T>[];
  valor: T;
  onChange: (v: T) => void;
};

/** Controle segmentado (radiogroup de chips), com setas para trocar a opção e tabindex roving. */
export function Alternador<T extends string>({ rotulo, opcoes, valor, onChange }: Props<T>) {
  const indiceAtual = opcoes.findIndex((o) => o.valor === valor);

  function mover(delta: number) {
    const total = opcoes.length;
    const proximo = ((indiceAtual + delta) % total + total) % total;
    onChange(opcoes[proximo].valor);
  }

  function aoTeclar(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      mover(1);
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      mover(-1);
    }
  }

  return (
    <div role="radiogroup" aria-label={rotulo} className="text-sm">
      <div className="inline-flex flex-wrap gap-2">
        {opcoes.map((opcao) => {
          const ativo = opcao.valor === valor;
          return (
            <button
              key={opcao.valor}
              type="button"
              role="radio"
              data-slot="chip"
              aria-checked={ativo}
              tabIndex={ativo ? 0 : -1}
              onClick={() => onChange(opcao.valor)}
              onKeyDown={aoTeclar}
              className={cn(
                "inline-flex max-w-full items-center gap-2 rounded-full border px-3 py-1 text-left font-medium transition-colors",
                ativo
                  ? "border-primary bg-primary-soft text-primary"
                  : "border-line bg-panel text-[var(--text)] hover:bg-subtle",
              )}
            >
              {opcao.rotulo}
            </button>
          );
        })}
      </div>
    </div>
  );
}
