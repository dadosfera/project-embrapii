import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type Props = {
  id: string;
  anos: number[];
  de: number;
  ate: number;
  onChange: (de: number, ate: number) => void;
  disabled?: boolean;
  className?: string;
};

/** Dois seletores de ano ("De"/"Até") mais o atalho "Todos os anos", para o período das telas de evolução. */
export function PeriodoAnos({ id, anos, de, ate, onChange, disabled, className }: Props) {
  const min = anos[0];
  const max = anos[anos.length - 1];
  const anosAte = anos.filter((ano) => ano >= de);
  const todosOsAnos = de === min && ate === max;

  return (
    <fieldset className={className} disabled={disabled}>
      <legend className="block text-sm font-semibold text-[var(--text)]">Período</legend>

      <div className="mt-2 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor={`${id}-de`} className="block text-sm text-muted">
            De
          </label>
          <Select
            value={`${de}`}
            onValueChange={(v) => {
              const novoDe = Number(v);
              // Se o novo "De" passar do "Até" atual, o "Até" acompanha para o mesmo ano
              // (nunca um intervalo invertido) em vez de deixar a UI num estado inconsistente.
              onChange(novoDe, novoDe > ate ? novoDe : ate);
            }}
          >
            <SelectTrigger id={`${id}-de`} className="mt-2 h-10 w-fit bg-panel data-[size=default]:h-10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent position="popper">
              {anos.map((ano) => (
                <SelectItem key={ano} value={`${ano}`}>
                  {ano}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <label htmlFor={`${id}-ate`} className="block text-sm text-muted">
            Até
          </label>
          <Select value={`${ate}`} onValueChange={(v) => onChange(de, Number(v))}>
            <SelectTrigger id={`${id}-ate`} className="mt-2 h-10 w-fit bg-panel data-[size=default]:h-10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent position="popper">
              {anosAte.map((ano) => (
                <SelectItem key={ano} value={`${ano}`}>
                  {ano}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          type="button"
          variant="outline"
          size="sm"
          aria-pressed={todosOsAnos}
          onClick={() => onChange(min, max)}
        >
          Todos os anos
        </Button>
      </div>
    </fieldset>
  );
}
