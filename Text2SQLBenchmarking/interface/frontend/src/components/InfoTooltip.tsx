import { Icon } from "./Icon";

export function InfoTooltip({ id, label, children }: { id: string; label: string; children: string }) {
  return (
    <span className="tooltip">
      <button type="button" className="icon-button tooltip-trigger" aria-label={`Sobre ${label}`} aria-describedby={id}>
        <Icon name="info" size={16} />
      </button>
      <span className="tooltip-content" id={id} role="tooltip">{children}</span>
    </span>
  );
}
