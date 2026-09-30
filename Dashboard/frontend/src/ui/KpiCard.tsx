import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { SEM_DADO, numeroExato } from "./format";

type Props = {
  label: string;
  value: number | null | undefined;
  format: (v: number | null | undefined) => string;
  exact?: (v: number | null | undefined) => string;
  hint?: string;
  loading?: boolean;
  destaque?: boolean;
};

export function KpiCard({ label, value, format, exact = numeroExato, hint, loading, destaque }: Props) {
  const texto = format(value);
  const vazio = value == null || Number.isNaN(value);
  return (
    <article
      className={cn(
        "rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-5",
        destaque && "border-primary bg-primary-tint",
      )}
    >
      <p className="text-sm font-medium text-muted">{label}</p>
      {loading ? (
        <Skeleton className="mt-3 h-8 w-32" />
      ) : vazio ? (
        <p className="mt-3 text-2xl font-semibold text-muted">{SEM_DADO}</p>
      ) : (
        <Tooltip>
          <TooltipTrigger asChild>
            {/* aria-label não é permitido em <p> sem role (axe aria-prohibited-attr). O rótulo visível acima
                já é lido; aqui o leitor ouve só o valor exato, e o compacto fica fora da árvore de acessibilidade.
                aria-describedby={undefined} impede o Radix de apontar para o conteúdo do tooltip, que repete o valor. */}
            <p
              tabIndex={0}
              aria-describedby={undefined}
              className={cn(
                "mt-3 w-fit cursor-default font-bold tabular-nums text-[var(--text)]",
                destaque ? "text-3xl sm:text-4xl" : "text-2xl sm:text-3xl",
              )}
            >
              <span aria-hidden="true">{texto}</span>
              <span className="sr-only">{exact(value)}</span>
            </p>
          </TooltipTrigger>
          <TooltipContent>{exact(value)}</TooltipContent>
        </Tooltip>
      )}
      {hint ? <p className="mt-2 text-xs text-muted">{hint}</p> : null}
    </article>
  );
}
