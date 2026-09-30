import type { ReactNode } from "react";

type Props = {
  title: string;
  subtitle?: ReactNode;
  source?: string;
  legend?: ReactNode;
  children: ReactNode;
  /** Nível do título. Use "h3" quando o gráfico estiver dentro de uma seção que já tem h2. */
  as?: "h2" | "h3";
};

export function ChartFrame({ title, subtitle, source, legend, children, as: Titulo = "h2" }: Props) {
  return (
    <section className="rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-5">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          <Titulo className="text-lg font-semibold text-[var(--text)]">{title}</Titulo>
          {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
        </div>
        {legend}
      </header>
      {children}
      {source ? <p className="mt-3 text-xs text-muted">Fonte: {source}</p> : null}
    </section>
  );
}
