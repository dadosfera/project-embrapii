import type { SystemStatus } from "../api/types";

const operationLabels: Record<string, string> = {
  LOAD_RUNTIME: "Preparando modelo e recursos...",
  GENERATE: "Gerando consultas...",
  CHAT: "Gerando consulta...",
  EXECUTE_SQL: "Executando consulta...",
  BENCHMARK: "Benchmark em execução...",
  EXPIRE_RUNTIME: "Liberando modelo...",
  SHUTDOWN: "Encerrando serviço..."
};

export function OperationStatus({
  status,
  chatActive,
  benchmarkActive
}: {
  status: SystemStatus | null;
  chatActive: boolean;
  benchmarkActive: boolean;
}) {
  const activeOperation = status?.is_busy ? status.active_operation : null;
  const label = activeOperation
    ? operationLabels[activeOperation] || "Operação em andamento..."
    : benchmarkActive
      ? "Benchmark em execução..."
      : chatActive
        ? "Gerando consulta..."
        : null;

  if (!label) return <span className="header-status-slot" aria-hidden="true" />;
  return (
    <p className="operation-status" role="status" aria-live="polite">
      <span className="status-dot" aria-hidden="true" />
      {label}
    </p>
  );
}
