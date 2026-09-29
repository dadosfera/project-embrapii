import type { EscalaMapa } from "./escalaMapa";
import { rotuloFaixa } from "./escalaMapa";

type Props = {
  escala: EscalaMapa;
  cores: string[];
  unidade: string;
  formatar: (v: number) => string;
  mostrarSemRegistro?: boolean;
  mostrarZero?: boolean;
};

/** Amostra de 14x14px, decorativa (o texto ao lado já descreve a faixa). */
function Amostra({ className }: { className: string }) {
  return <span aria-hidden="true" className={`inline-block h-[14px] w-[14px] shrink-0 border border-line ${className}`} />;
}

export function ChoroplethLegend({ escala, cores, unidade, formatar, mostrarSemRegistro, mostrarZero }: Props) {
  return (
    <figure>
      <figcaption className="tabular-nums text-xs text-muted">Legenda ({unidade})</figcaption>
      <ul className="mt-2 flex flex-col gap-1">
        {mostrarSemRegistro ? (
          <li className="flex items-center gap-2">
            <Amostra className="hachura-sem-registro" />
            <span className="tabular-nums text-xs text-muted">sem registro</span>
          </li>
        ) : null}
        {mostrarZero ? (
          <li className="flex items-center gap-2">
            <Amostra className="bg-subtle" />
            <span className="tabular-nums text-xs text-muted">0</span>
          </li>
        ) : null}
        {escala.faixas.map((f, i) => (
          <li key={f.indice} className="flex items-center gap-2">
            <span aria-hidden="true" className="inline-block h-[14px] w-[14px] shrink-0" style={{ background: cores[i] }} />
            <span className="tabular-nums text-xs text-muted">{rotuloFaixa(f, formatar)}</span>
          </li>
        ))}
      </ul>
    </figure>
  );
}
