import { NavLink } from "react-router";

import { preCarregarRota, type RotaConhecida } from "../rotas";
import { ShellIcon } from "./ShellIcon";
import type { ShellIconName } from "./icons-shell";

const DESTINOS: { to: RotaConhecida; label: string; icon: ShellIconName; end?: boolean }[] = [
  { to: "/", label: "Início", icon: "home", end: true },
  { to: "/medicamentos", label: "Medicamentos", icon: "droplet" },
  { to: "/compras", label: "Compras", icon: "cart" },
  { to: "/leitos", label: "Leitos", icon: "activity" },
  { to: "/mapa", label: "Mapa", icon: "map" },
  { to: "/fornecedores", label: "Fornecedores", icon: "briefcase" },
];

function linkClass({ isActive }: { isActive: boolean }) {
  return [
    "inline-flex min-h-10 items-center gap-2 rounded-[var(--radius-sm)] px-3 text-sm font-semibold transition-colors",
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]",
    isActive ? "bg-primary-soft text-primary" : "text-muted hover:bg-subtle hover:text-[var(--text)]",
  ].join(" ");
}

export function Navegacao({
  onNavigate,
  aoNavegar,
}: {
  onNavigate?: () => void;
  /** Chamado ao clicar num destino, antes da navegação real: dispara a BarraDeProgresso (App.tsx). */
  aoNavegar?: (destino: string) => void;
}) {
  return (
    <>
      {DESTINOS.map((d) => (
        <NavLink
          key={d.to}
          to={d.to}
          end={d.end}
          className={linkClass}
          onPointerEnter={() => preCarregarRota(d.to)}
          onFocus={() => preCarregarRota(d.to)}
          onClick={() => {
            aoNavegar?.(d.to);
            onNavigate?.();
          }}
        >
          <ShellIcon name={d.icon} size={18} />
          {d.label}
        </NavLink>
      ))}
    </>
  );
}
