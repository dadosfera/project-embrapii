import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { apiClient, PublicApiError, RequestCancelledError } from "../../api/client";
import type { BenchmarkJob, BenchmarkJobState, BenchmarkResult, CatalogResponse, ConfigurationSelection, ExperimentStatus, MetricMetadata, MetricValue, PublicError } from "../../api/types";
import { ConfigurationSummary } from "../../components/ConfigurationSummary";
import { Icon } from "../../components/Icon";
import { InfoTooltip } from "../../components/InfoTooltip";
import { PublicErrorNotice } from "../../components/PublicErrorNotice";

const activeStates: BenchmarkJobState[] = ["accepted", "archiving", "loading_model", "generating", "generation_completed", "executing", "calculating_metrics"];
const stateLabels: Record<BenchmarkJobState, string> = {
  accepted: "Preparando Benchmark...",
  archiving: "Validando e arquivando o resultado anterior...",
  loading_model: "Preparando modelo e recursos...",
  generating: "Gerando consultas...",
  generation_completed: "Geração concluída",
  executing: "Executando e comparando consultas...",
  calculating_metrics: "Calculando métricas agregadas...",
  completed: "Benchmark concluído",
  failed: "Benchmark falhou",
  interrupted: "Benchmark interrompido"
};

const isActive = (state: BenchmarkJobState) => activeStates.includes(state);
const toPublicError = (reason: unknown, fallback: string): PublicError => reason instanceof PublicApiError
  ? { code: reason.code, message: reason.message, retryable: reason.retryable }
  : { code: "INTERNAL_ERROR", message: fallback, retryable: false };
const sameConfiguration = (left: ConfigurationSelection, right: ConfigurationSelection) => (
  left.database === right.database
  && left.library === right.library
  && left.model_id === right.model_id
  && left.context === right.context
);
const number = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 3 });
const percent = new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2 });
const noop = () => undefined;

const countDefinitions = {
  correct: "O resultado produzido coincide com a referência.",
  incorrect: "A consulta foi executada, mas o resultado obtido foi diferente da referência.",
  errors: "Consultas que falharam durante a execução.",
  timeouts: "Subconjunto dos erros interrompidos pelo limite de tempo."
};

function formatMetric(metric: MetricValue | undefined, metadata: MetricMetadata) {
  if (!metric?.available || metric.value === null) return "—";
  if (metadata.format === "percentage") return percent.format(metric.value);
  return number.format(metric.value);
}

function BenchmarkResults({ result, catalog }: { result: BenchmarkResult; catalog: CatalogResponse }) {
  const visibleMetrics = catalog.metrics
    .filter((metadata) => metadata.initially_visible)
    .sort((left, right) => left.order - right.order);
  const primaryMetadata = visibleMetrics.find((metadata) => metadata.prominence === "primary");
  const secondaryMetadata = visibleMetrics.filter((metadata) => metadata.prominence === "secondary");
  const primaryMetric = primaryMetadata ? result.metrics?.[primaryMetadata.key] : undefined;
  if (!result.counts || !result.times || !primaryMetadata || !primaryMetric) return null;
  const counts = result.counts;
  const times = result.times;
  const total = counts.total || 1;
  const timeEntries = [
    ["Geração", times.generation],
    ["Execução da referência", times.execution_ground_truth],
    ["Execução da consulta gerada", times.execution_generated]
  ] as const;
  const largestTime = Math.max(...timeEntries.map(([, value]) => value), 1);

  const countItems = [
    { key: "total", label: "Total", value: counts.total },
    { key: "correct", label: "Corretas", value: counts.correct, tooltip: countDefinitions.correct },
    { key: "incorrect", label: "Incorretas sem erro", value: counts.incorrect_without_error, tooltip: countDefinitions.incorrect },
    { key: "errors", label: "Erros", value: counts.errors, tooltip: countDefinitions.errors },
    { key: "timeouts", label: "Timeouts", value: counts.timeouts, tooltip: countDefinitions.timeouts }
  ];

  const distribution = [
    { key: "correct", label: "Corretas", value: counts.correct, className: "distribution-correct" },
    { key: "incorrect", label: "Incorretas sem erro", value: counts.incorrect_without_error, className: "distribution-incorrect" },
    { key: "errors", label: "Erros", value: counts.errors, className: "distribution-error" }
  ];

  return (
    <div className="benchmark-results">
      <section className="execution-results" aria-labelledby="execution-accuracy-title">
        <div className="metric-primary">
          <div className="section-title-row">
            <h3 id="execution-accuracy-title">{primaryMetadata.label}</h3>
            <InfoTooltip id="execution-accuracy-tooltip" label={primaryMetadata.label}>
              {primaryMetadata.description}
            </InfoTooltip>
          </div>
          <p className="metric-value">{formatMetric(primaryMetric, primaryMetadata)}</p>
          <p className="metric-caption">{primaryMetric.numerator} de {primaryMetric.denominator} consultas corretas</p>
        </div>

        <dl className="benchmark-counts" aria-label="Contagens da Acurácia de Execução">
          {countItems.map((item) => (
            <div key={item.key}>
              <dt>
                {item.label}
                {item.tooltip && <InfoTooltip id={`count-${item.key}-tooltip`} label={item.label}>{item.tooltip}</InfoTooltip>}
              </dt>
              <dd>{number.format(item.value)}</dd>
              {item.key === "timeouts" && <small>Subconjunto de erros</small>}
            </div>
          ))}
        </dl>

        <section className="benchmark-section" aria-labelledby="distribution-title">
          <h3 id="distribution-title">Distribuição dos resultados</h3>
          {counts.total === 0 ? <p className="benchmark-empty">Não há linhas para distribuir.</p> : (
            <div className="distribution-bar" role="img" aria-label={`${counts.correct} corretas, ${counts.incorrect_without_error} incorretas sem erro e ${counts.errors} erros`}>
              {distribution.map((item) => (
                <span
                  className={item.className}
                  style={{ "--segment-width": `${(item.value / total) * 100}%` } as CSSProperties}
                  key={item.key}
                />
              ))}
            </div>
          )}
          <ul className="distribution-legend" aria-label="Legenda da distribuição">
            {distribution.map((item) => (
              <li key={item.key}><span className={`legend-swatch ${item.className}`} aria-hidden="true" /><span>{item.label}</span><strong>{number.format(item.value)}</strong></li>
            ))}
          </ul>
        </section>
      </section>

      <section className="additional-metrics" aria-labelledby="additional-metrics-title">
        <h3 id="additional-metrics-title">Outras métricas</h3>
        <div className="metric-secondary-grid" aria-label="Métricas secundárias">
          {secondaryMetadata.map((metadata) => {
            const metric = result.metrics?.[metadata.key];
            const hasPartialCoverage = metric && metric.denominator !== counts.total;
            return (
              <div className="metric-secondary" key={metadata.key}>
                <div className="section-title-row">
                  <h3>{metadata.label}</h3>
                  <InfoTooltip id={`metric-${metadata.key}-tooltip`} label={metadata.label}>{metadata.description}</InfoTooltip>
                </div>
                <p className="metric-secondary-value">{formatMetric(metric, metadata)}</p>
                {hasPartialCoverage && <p className="metric-secondary-caption">Cobertura: {metric.denominator} de {counts.total} consultas</p>}
              </div>
            );
          })}
        </div>
      </section>

      <section className="benchmark-section" aria-labelledby="times-title">
        <h3 id="times-title">Tempos registrados</h3>
        <div className="time-bars">
          {timeEntries.map(([label, value]) => (
            <div className="time-row" key={label}>
              <span>{label}</span>
              <span className="time-track" aria-hidden="true"><i style={{ "--time-width": `${(value / largestTime) * 100}%` } as CSSProperties} /></span>
              <strong>{number.format(value)} s</strong>
            </div>
          ))}
        </div>
        <dl className="benchmark-time-summary">
          <div><dt>Execução total</dt><dd>{number.format(times.execution_total)} s</dd></div>
          <div>
            <dt>Tempo registrado total <InfoTooltip id="recorded-total-tooltip" label="Tempo registrado total">Soma dos tempos persistidos; não representa duração real de parede.</InfoTooltip></dt>
            <dd>{number.format(times.recorded_total)} s</dd>
          </div>
        </dl>
        <p className="benchmark-note">O tempo registrado total soma os tempos persistidos e não representa a duração real de parede.</p>
      </section>

      <details className="metrics-glossary">
        <summary>Entenda as métricas</summary>
        <div className="metrics-glossary-body">
          <dl>
            {visibleMetrics.map((metadata) => (
              <div key={metadata.key}><dt>{metadata.label}</dt><dd>{metadata.description}</dd></div>
            ))}
            <div><dt>Corretas</dt><dd>{countDefinitions.correct}</dd></div>
            <div><dt>Incorretas sem erro</dt><dd>{countDefinitions.incorrect}</dd></div>
            <div><dt>Erros</dt><dd>{countDefinitions.errors}</dd></div>
            <div><dt>Timeouts</dt><dd>{countDefinitions.timeouts}</dd></div>
          </dl>
        </div>
      </details>
    </div>
  );
}

interface Props {
  configuration: ConfigurationSelection;
  catalog: CatalogResponse;
  seed?: number;
  onSeedChange?: (seed: number) => void;
  activeBenchmarkJob?: BenchmarkJob | null;
  onBenchmarkRecovered?: (job: BenchmarkJob) => void;
  onActivityChange: (value: boolean) => void;
  onVisibleChange: (value: boolean) => void;
  onOpenConfiguration?: () => void;
}

export function BenchmarkPlaceholder({
  configuration,
  catalog,
  seed = 42,
  onSeedChange = noop,
  activeBenchmarkJob = null,
  onBenchmarkRecovered,
  onActivityChange,
  onVisibleChange,
  onOpenConfiguration = noop
}: Props) {
  const [experiment, setExperiment] = useState<ExperimentStatus | null>(null);
  const [job, setJob] = useState<BenchmarkJob | null>(activeBenchmarkJob);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<PublicError | null>(null);
  const [refreshVersion, setRefreshVersion] = useState(0);
  const [reexecutionOpen, setReexecutionOpen] = useState(false);
  const selectionRequest = useRef<AbortController | null>(null);
  const confirmButton = useRef<HTMLButtonElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  const trackedJob = activeBenchmarkJob && activeBenchmarkJob.job_id !== job?.job_id
    ? activeBenchmarkJob
    : job || activeBenchmarkJob;
  const trackedIdentity = trackedJob && (isActive(trackedJob.state) || sameConfiguration(trackedJob.configuration, configuration))
    ? trackedJob
    : null;
  const benchmarkConfiguration = trackedIdentity?.configuration ?? configuration;
  const benchmarkDatabase = benchmarkConfiguration.database;
  const benchmarkLibrary = benchmarkConfiguration.library;
  const benchmarkModelId = benchmarkConfiguration.model_id;
  const benchmarkContext = benchmarkConfiguration.context;
  const benchmarkSeed = trackedIdentity?.seed ?? seed;
  const jobActive = Boolean(trackedJob && isActive(trackedJob.state));
  const visibleExperiment = useMemo(() => (
    experiment
    && sameConfiguration(experiment.configuration, benchmarkConfiguration)
    && experiment.seed === benchmarkSeed
      ? experiment
      : null
  ), [benchmarkConfiguration, benchmarkSeed, experiment]);

  useEffect(() => {
    if (!activeBenchmarkJob) return;
    onSeedChange(activeBenchmarkJob.seed);
    setJob((current) => current?.job_id === activeBenchmarkJob.job_id && !isActive(current.state)
      ? current
      : activeBenchmarkJob);
  }, [activeBenchmarkJob, onSeedChange]);

  useEffect(() => {
    if (!reexecutionOpen) return;
    previousFocus.current = document.activeElement as HTMLElement | null;
    confirmButton.current?.focus();
    return () => previousFocus.current?.focus();
  }, [reexecutionOpen]);

  useEffect(() => {
    setJob((current) => current && !isActive(current.state) && !sameConfiguration(current.configuration, configuration)
      ? null
      : current);
  }, [configuration]);

  useEffect(() => onActivityChange(submitting || jobActive), [jobActive, onActivityChange, submitting]);
  useEffect(() => onVisibleChange(Boolean(trackedJob || error || (visibleExperiment && visibleExperiment.artifact_state !== "not_started"))), [error, onVisibleChange, trackedJob, visibleExperiment]);
  useEffect(() => setError(null), [benchmarkContext, benchmarkDatabase, benchmarkLibrary, benchmarkModelId, benchmarkSeed]);

  useEffect(() => {
    selectionRequest.current?.abort();
    const controller = new AbortController();
    selectionRequest.current = controller;
    setLoading(true);
    Promise.all([
      apiClient.getBenchmarkStatus({
        database: benchmarkDatabase,
        library: benchmarkLibrary,
        model_id: benchmarkModelId,
        context: benchmarkContext
      }, benchmarkSeed, controller.signal),
      apiClient.getActiveBenchmark(controller.signal)
    ]).then(([status, active]) => {
      if (selectionRequest.current !== controller) return;
      const recoveredJob = active.job;
      if (recoveredJob && isActive(recoveredJob.state)) {
        onSeedChange(recoveredJob.seed);
        setJob((current) => current && current.job_id === recoveredJob.job_id && !isActive(current.state) ? current : recoveredJob);
        onBenchmarkRecovered?.(recoveredJob);
        if (!sameConfiguration(status.configuration, recoveredJob.configuration) || status.seed !== recoveredJob.seed) {
          setExperiment(null);
          return;
        }
      }
      setExperiment(status);
    }).catch((reason: unknown) => {
      if (reason instanceof RequestCancelledError || selectionRequest.current !== controller) return;
      setError(toPublicError(reason, "Não foi possível consultar o Benchmark."));
    }).finally(() => {
      if (selectionRequest.current === controller) {
        selectionRequest.current = null;
        setLoading(false);
      }
    });
    return () => controller.abort();
  }, [benchmarkContext, benchmarkDatabase, benchmarkLibrary, benchmarkModelId, benchmarkSeed, onBenchmarkRecovered, onSeedChange, refreshVersion]);

  useEffect(() => {
    if (!trackedJob || !isActive(trackedJob.state)) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      apiClient.getBenchmark(trackedJob.job_id, controller.signal).then(({ job: next }) => {
        setJob(next);
        if (!isActive(next.state)) {
          setExperiment(null);
          setLoading(true);
          setRefreshVersion((value) => value + 1);
        }
      }).catch((reason: unknown) => {
        if (reason instanceof RequestCancelledError) return;
        setError(toPublicError(reason, "Não foi possível acompanhar o Benchmark."));
      });
    }, 500);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [trackedJob]);

  const submit = async (action: "run_missing_stages" | "reexecute", confirmed = false) => {
    if (submitting || jobActive) return;
    if (action === "reexecute" && !confirmed) {
      setReexecutionOpen(true);
      return;
    }
    setSubmitting(true);
    setError(null);
    const controller = new AbortController();
    let confirmationToken: string | undefined;
    try {
      if (action === "reexecute") {
        const intent = await apiClient.createReexecutionIntent(benchmarkConfiguration, benchmarkSeed, controller.signal);
        confirmationToken = intent.confirmationToken;
      }
      const accepted = await apiClient.createBenchmark(benchmarkConfiguration, benchmarkSeed, action, confirmationToken, controller.signal);
      confirmationToken = undefined;
      setJob(accepted.snapshot);
    } catch (reason) {
      if (!(reason instanceof RequestCancelledError)) {
        const publicError = toPublicError(reason, "Não foi possível iniciar o Benchmark.");
        setError(publicError);
        if (publicError.code === "REEXECUTION_STATE_CHANGED") setRefreshVersion((value) => value + 1);
      }
    } finally {
      confirmationToken = undefined;
      setSubmitting(false);
    }
  };

  const result = useMemo<BenchmarkResult | null>(() => {
    if (visibleExperiment?.artifact_state === "complete" && visibleExperiment.metrics && visibleExperiment.counts && visibleExperiment.times) return visibleExperiment;
    return null;
  }, [visibleExperiment]);

  return (
    <section className="benchmark-workspace" aria-labelledby="benchmark-title">
      <header className="benchmark-header">
        <h2 id="benchmark-title">Benchmark</h2>
        <p>Acompanhe a execução e compare os resultados da configuração selecionada.</p>
        <ConfigurationSummary configuration={benchmarkConfiguration} catalog={catalog} seed={benchmarkSeed} onOpen={onOpenConfiguration} />
      </header>

      {error && (
        <div className="benchmark-error-wrap">
          <PublicErrorNotice
            error={error}
            title="Não foi possível atualizar o Benchmark"
            onRetry={() => { setError(null); setRefreshVersion((value) => value + 1); }}
            retryLabel="Consultar novamente"
            className="benchmark-error"
          />
          {error.code === "REEXECUTION_STATE_CHANGED" && <button className="secondary-button" type="button" onClick={() => { setError(null); setRefreshVersion((value) => value + 1); }}>Atualizar artefatos para nova confirmação</button>}
        </div>
      )}
      {loading && <p className="benchmark-loading" aria-live="polite"><span className="query-loader" aria-hidden="true" />Consultando artefatos e job ativo...</p>}

      {trackedJob && isActive(trackedJob.state) && (
        <section className="benchmark-progress" aria-live="polite">
          <span className="progress-mark" aria-hidden="true"><span /></span>
          <div><h3>Operação em andamento</h3><p>{stateLabels[trackedJob.state]}</p></div>
        </section>
      )}
      {trackedJob && (trackedJob.state === "failed" || trackedJob.state === "interrupted") && (
        <PublicErrorNotice
          error={trackedJob.error || { code: "INTERNAL_ERROR", message: "A operação não foi concluída.", retryable: false }}
          title={stateLabels[trackedJob.state]}
          onRetry={() => { setJob(null); setRefreshVersion((value) => value + 1); }}
          retryLabel="Consultar artefatos para nova tentativa"
          className="benchmark-error"
        />
      )}

      {!loading && visibleExperiment?.artifact_state === "not_started" && !jobActive && (
        <section className="benchmark-state">
          <div><h3>Benchmark ainda não executado</h3><p>Não há artefatos para esta configuração e seed.</p></div>
          <button className="primary-button" type="button" disabled={submitting} onClick={() => { void submit("run_missing_stages"); }}>Executar benchmark</button>
        </section>
      )}
      {!loading && visibleExperiment?.artifact_state === "generation_only" && !jobActive && (
        <section className="benchmark-state">
          <div><h3>Geração disponível</h3><p>A geração existente será preservada. Somente execução e métricas serão realizadas.</p></div>
          <button className="primary-button" type="button" disabled={submitting} onClick={() => { void submit("run_missing_stages"); }}>Executar etapas faltantes</button>
        </section>
      )}
      {!loading && visibleExperiment?.artifact_state === "invalid_result" && (
        <PublicErrorNotice
          error={{ code: "INVALID_PARQUET", message: visibleExperiment.invalid_reason || "Os artefatos não podem ser usados com segurança.", retryable: false }}
          title="Resultado inválido"
          className="benchmark-error"
        />
      )}

      {result && (
        <>
          <BenchmarkResults result={result} catalog={catalog} />
          <div className="benchmark-actions"><button type="button" className="danger-secondary-button" disabled={submitting || jobActive} onClick={() => { void submit("reexecute"); }}>Reexecutar benchmark</button></div>
        </>
      )}

      {reexecutionOpen && (
        <div className="dialog-backdrop" role="presentation">
          <section className="confirmation-dialog" role="dialog" aria-modal="true" aria-labelledby="reexecution-title" aria-describedby="reexecution-description" onKeyDown={(event) => {
            if (event.key === "Escape") {
              setReexecutionOpen(false);
              return;
            }
            if (event.key !== "Tab") return;
            const buttons = Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>("button:not(:disabled)"));
            const first = buttons[0];
            const last = buttons[buttons.length - 1];
            if (event.shiftKey && document.activeElement === first) {
              event.preventDefault();
              last?.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
              event.preventDefault();
              first?.focus();
            }
          }}>
            <div className="dialog-icon" aria-hidden="true"><Icon name="database" /></div>
            <button type="button" className="icon-button dialog-close" aria-label="Cancelar reexecução" onClick={() => setReexecutionOpen(false)}><Icon name="close" /></button>
            <h2 id="reexecution-title">Reexecutar este Benchmark?</h2>
            <p id="reexecution-description">O resultado atual será arquivado antes da reexecução. Esta ação exige uma nova confirmação segura.</p>
            <div className="dialog-actions">
              <button type="button" className="secondary-button" onClick={() => setReexecutionOpen(false)}>Cancelar</button>
              <button ref={confirmButton} type="button" className="danger-button" onClick={() => {
                setReexecutionOpen(false);
                void submit("reexecute", true);
              }}>Arquivar e reexecutar</button>
            </div>
          </section>
        </div>
      )}
    </section>
  );
}
