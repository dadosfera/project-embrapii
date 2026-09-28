import type { ReactNode } from "react";
import { Icon } from "./Icon";

type Props = { title: string; cause: ReactNode; action?: ReactNode };

export function EmptyState({ title, cause, action }: Props) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-[var(--radius-md)] border border-dashed border-line bg-surface px-6 py-10 text-center">
      <Icon name="inbox" size={28} className="text-muted" />
      <p className="font-semibold text-[var(--text)]">{title}</p>
      <p className="max-w-md text-sm text-muted">{cause}</p>
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}
