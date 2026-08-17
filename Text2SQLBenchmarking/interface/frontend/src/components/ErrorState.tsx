import type { PublicError } from "../api/types";
import { PublicErrorNotice } from "./PublicErrorNotice";

export function ErrorState({ error, onRetry }: { error: PublicError; onRetry: () => void }) {
  return (
    <div className="state-panel state-error">
      <PublicErrorNotice
        error={error}
        title="Não foi possível iniciar a interface"
        onRetry={onRetry}
      />
    </div>
  );
}
