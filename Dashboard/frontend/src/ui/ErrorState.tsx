import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/http";
import { Icon } from "./Icon";

type Props = { error: unknown; onRetry?: () => void };

export function ErrorState({ error, onRetry }: Props) {
  const msg = error instanceof ApiError ? error.message : "Não foi possível carregar os dados.";
  return (
    <div role="alert" className="flex flex-col items-center gap-2 rounded-[var(--radius-md)] border border-[var(--danger)] bg-[var(--danger-soft)] px-6 py-8 text-center">
      <Icon name="alert" size={28} className="text-[var(--danger)]" />
      <p className="font-semibold text-[var(--text)]">Não foi possível carregar</p>
      <p className="max-w-md text-sm text-muted">{msg}</p>
      {onRetry ? (
        <Button variant="outline" onClick={onRetry} className="mt-2">
          <Icon name="refresh" size={16} /> Tentar de novo
        </Button>
      ) : null}
    </div>
  );
}
