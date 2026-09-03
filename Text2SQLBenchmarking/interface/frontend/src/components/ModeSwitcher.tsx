import type { Mode } from "../api/types";

interface Props {
  mode: Mode;
  disabled: boolean;
  onChange: (mode: Mode) => void;
}

export function ModeSwitcher({ mode, disabled, onChange }: Props) {
  const items: { id: Mode; label: string }[] = [
    { id: "chat", label: "Chat SQL" },
    { id: "benchmark", label: "Benchmark" }
  ];

  return (
    <nav className="mode-switcher" aria-label="Navegação principal">
      {items.map((item) => (
        <button
          key={item.id}
          type="button"
          disabled={disabled}
          aria-current={mode === item.id ? "page" : undefined}
          className={mode === item.id ? "is-active" : ""}
          onClick={() => onChange(item.id)}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
