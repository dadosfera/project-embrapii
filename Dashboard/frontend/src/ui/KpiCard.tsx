import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { SEM_DADO, numeroExato } from "./format";

type Props = {
  label: string;
  value: number | null | undefined;
  format: (v: number | null | undefined) => string;
  exact?: (v: number | null | undefined) => string;
  hint?: string;
  loading?: boolean;
};

export function KpiCard({ label, value, format, exact = numeroExato, hint, loading }: Props) {
  const texto = format(value);
  const vazio = texto === SEM_DADO;
  return (
    <article className="rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-5">
      <p className="text-sm font-medium text-muted">{label}</p>
      {loading ? (
        <Skeleton className="mt-3 h-8 w-32" />
      ) : vazio ? (
        <p className="mt-3 text-2xl font-semibold text-muted">{SEM_DADO}</p>
      ) : (
        <Tooltip>
          <TooltipTrigger asChild>
            <p className="mt-3 w-fit cursor-default text-2xl font-bold tabular-nums text-[var(--text)] sm:text-3xl">{texto}</p>
          </TooltipTrigger>
          <TooltipContent>{exact(value)}</TooltipContent>
        </Tooltip>
      )}
      {hint ? <p className="mt-2 text-xs text-muted">{hint}</p> : null}
    </article>
  );
}
