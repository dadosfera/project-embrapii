import type { PublicError } from "../api/types";
import { Icon } from "./Icon";

const guidanceByCode: Record<string, string> = {
  RESOURCE_BUSY: "Há outra operação em andamento. Aguarde a conclusão antes de enviar novamente.",
  QUERY_TIMEOUT: "A consulta foi interrompida pelo limite de tempo; nenhuma repetição automática será feita.",
  DATABASE_CONNECTION_ERROR: "A conexão interna não foi exposta. Verifique a disponibilidade do serviço antes de uma nova tentativa.",
  INVALID_PARQUET: "Nenhum arquivo será sobrescrito.",
  REEXECUTION_STATE_CHANGED: "Os artefatos mudaram desde a confirmação. Revise o resultado e confirme novamente.",
  ARCHIVE_ERROR: "Os artefatos existentes foram preservados; revise o armazenamento antes de reexecutar.",
  INTERNAL_ERROR: "O detalhe técnico foi mantido apenas nos logs seguros do servidor."
};

interface Props {
  error: PublicError;
  title?: string;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
}

export function PublicErrorNotice({ error, title = "Não foi possível concluir a operação", onRetry, retryLabel = "Tentar novamente", className = "" }: Props) {
  const guidance = guidanceByCode[error.code];
  return (
    <section className={`public-error ${className}`.trim()} role="alert">
      <div className="public-error-heading">
        <span className="public-error-icon" aria-hidden="true"><Icon name="info" size={18} /></span>
        <h3>{title}</h3>
      </div>
      <p className="public-error-message">{error.message}</p>
      {guidance && <p className="public-error-guidance">{guidance}</p>}
      <p className="public-error-code">Código: <code>{error.code}</code></p>
      {error.retryable && onRetry && <button className="secondary-button" type="button" onClick={onRetry}>{retryLabel}</button>}
    </section>
  );
}
