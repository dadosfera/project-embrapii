import { Button } from "@/components/ui/button";

type Props = {
  carregando: boolean;
  pendente?: boolean;
  type?: "submit" | "button";
  onClick?: () => void;
  ariaLabel?: string;
  className?: string;
};

/** Botão "Aplicar" dos filtros com aplicação manual: o rótulo não muda durante a carga. */
export function BotaoAplicar({ carregando, pendente, type = "submit", onClick, ariaLabel, className }: Props) {
  return (
    <div className={className}>
      <Button type={type} onClick={onClick} disabled={carregando} aria-busy={carregando} aria-label={ariaLabel}>
        Aplicar
      </Button>
      {pendente ? <p role="status" className="text-sm text-muted">Há alterações não aplicadas.</p> : null}
    </div>
  );
}
