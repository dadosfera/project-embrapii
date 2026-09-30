import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { UFS, nomeUf } from "../lib/ufs";

const TODAS = "Todas";

type Props = {
  id: string;
  label: string;
  /** "" = todas as UFs. */
  value: string;
  onChange: (uf: string) => void;
  disabled?: boolean;
  className?: string;
};

/** Select de UF reutilizável (Compras e Fornecedores): "Todas" + as 27 UFs de src/lib/ufs.ts, como "SP · São Paulo". */
export function SeletorUf({ id, label, value, onChange, disabled, className }: Props) {
  return (
    <div className={className}>
      <label htmlFor={id} className="block text-sm font-semibold text-[var(--text)]">
        {label}
      </label>

      <Select
        value={value || TODAS}
        onValueChange={(v) => onChange(v === TODAS ? "" : v)}
        disabled={disabled}
      >
        <SelectTrigger id={id} className="mt-2 h-10 w-full bg-panel data-[size=default]:h-10">
          <SelectValue />
        </SelectTrigger>

        <SelectContent position="popper">
          <SelectItem value={TODAS}>Todas</SelectItem>
          {UFS.map((uf) => (
            <SelectItem key={uf} value={uf}>
              {uf} · {nomeUf(uf)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
