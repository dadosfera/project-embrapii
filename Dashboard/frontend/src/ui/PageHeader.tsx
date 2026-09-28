import type { ReactNode } from "react";
import { Icon } from "./Icon";
import type { IconName } from "./icons";

type Props = { icon: IconName; title: string; description?: ReactNode; actions?: ReactNode };

export function PageHeader({ icon, title, description, actions }: Props) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex items-start gap-3">
        <span className="mt-1 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-primary-soft text-primary">
          <Icon name={icon} size={22} />
        </span>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-[var(--text)] sm:text-3xl">{title}</h1>
          {description ? <p className="mt-1 max-w-3xl text-sm leading-6 text-muted sm:text-base">{description}</p> : null}
        </div>
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </header>
  );
}
