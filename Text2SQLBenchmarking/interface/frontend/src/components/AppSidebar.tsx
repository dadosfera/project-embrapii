import { Fragment, type ReactNode } from "react";
import type { Mode } from "../api/types";
import { Icon, type IconName } from "./Icon";

const railItems: { label: string; shortLabel: string; icon: IconName }[] = [
  { label: "Configuração geral", shortLabel: "Configuração", icon: "settings" },
  { label: "Base de dados", shortLabel: "Base de dados", icon: "database" },
  { label: "Biblioteca", shortLabel: "Biblioteca", icon: "library" },
  { label: "Modelo", shortLabel: "Modelo", icon: "model" },
  { label: "Contexto", shortLabel: "Contexto", icon: "context" }
];

export function AppSidebar({
  open,
  mode,
  onToggle,
  children
}: {
  open: boolean;
  mode: Mode;
  onToggle: () => void;
  children: ReactNode;
}) {
  const items = mode === "benchmark"
    ? [...railItems, { label: "Seed", shortLabel: "Seed", icon: "seed" as IconName }]
    : railItems;

  return (
    <Fragment>
      {open && <button type="button" className="sidebar-backdrop" aria-label="Fechar configuração" onClick={onToggle} />}
      <aside className={`app-sidebar ${open ? "is-open" : "is-collapsed"}`} aria-label="Configuração da interface">
        {open ? (
          <>
            <div className="sidebar-header">
              <div>
                <h2>Configuração</h2>
                <p>Aplicada à próxima operação</p>
              </div>
              <button
                className="icon-button sidebar-toggle"
                type="button"
                onClick={onToggle}
                aria-label="Recolher configuração"
                aria-expanded="true"
                aria-controls="sidebar-content"
              >
                <Icon name="chevron-left" />
              </button>
            </div>
            <div id="sidebar-content" className="sidebar-content">{children}</div>
          </>
        ) : (
          <nav className="sidebar-rail" aria-label="Abrir configuração">
            {items.map((item, index) => {
              const tooltipId = `rail-tooltip-${item.icon}`;
              return (
                <div className={`rail-item ${index === 0 ? "rail-primary" : ""}`} key={item.label}>
                  <button
                    type="button"
                    className="icon-button rail-button"
                    onClick={onToggle}
                    aria-label={item.label}
                    aria-describedby={tooltipId}
                    aria-expanded="false"
                  >
                    <Icon name={item.icon} />
                  </button>
                  <span className="rail-tooltip" id={tooltipId} role="tooltip">{item.shortLabel}</span>
                </div>
              );
            })}
          </nav>
        )}
      </aside>
    </Fragment>
  );
}
