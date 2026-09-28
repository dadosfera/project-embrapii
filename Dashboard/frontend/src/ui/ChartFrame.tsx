import type { ReactNode } from "react";

type Props = { title: string; subtitle?: ReactNode; source?: string; legend?: ReactNode; children: ReactNode };

export function ChartFrame({ title, subtitle, source, legend, children }: Props) {
  return (
    <section className="rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-5">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-[var(--text)]">{title}</h2>
          {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
        </div>
        {legend}
      </header>
      {children}
      {source ? <p className="mt-3 text-xs text-muted">Fonte: {source}</p> : null}
    </section>
  );
}
