export type Mode = "chat" | "benchmark";

export interface ConfigurationSelection {
  database: string;
  library: string;
  model_id: string;
  context: string;
}

export interface AvailabilityReason {
  code: string;
  message: string;
}

export interface Availability {
  available: boolean;
  reason: AvailabilityReason | null;
}

export interface CatalogLibrary {
  id: string;
  label: string;
  contexts: string[];
  model_ids: string[];
  availability: Record<Mode, Availability>;
  order: number;
}

export interface CatalogModel {
  id: string;
  label: string;
  family: string;
  order: number;
}

export interface CatalogOption {
  id: string;
  label: string;
}

export interface MetricMetadata {
  key: string;
  code: string;
  label: string;
  description: string;
  format: "percentage";
  order: number;
  prominence: "primary" | "secondary" | "detail";
  initially_visible: boolean;
  parquet_column: string | null;
}

export interface CatalogResponse {
  databases: CatalogOption[];
  libraries: CatalogLibrary[];
  models: CatalogModel[];
  contexts: CatalogOption[];
  metrics: MetricMetadata[];
  initial_configuration: ConfigurationSelection;
}

export interface SystemStatus {
  is_busy: boolean;
  active_operation: string | null;
  model_state: string;
  runtime_loaded: boolean;
  runtime_configuration: ConfigurationSelection | null;
  benchmark_job: BenchmarkJob | null;
}

export interface HealthResponse {
  status: string;
  api_version: string;
  journal_available: boolean;
}

export interface ApiErrorEnvelope {
  error: PublicError;
}

export interface PublicError {
  code: string;
  message: string;
  retryable: boolean;
}

export interface ChatJob {
  job_id: string; state: "accepted" | "loading_model" | "generating" | "validating_sql" | "executing" | "succeeded" | "failed" | "expired";
  configuration: ConfigurationSelection;
  sql: string | null; columns: string[] | null; rows: unknown[][] | null; rowCount: number | null; displayedRowCount: number | null; truncated: boolean | null;
  generationTimeSeconds: number | null; executionTimeSeconds: number | null; error: PublicError | null;
}

export type ArtifactState = "not_started" | "generation_only" | "complete" | "invalid_result";
export type BenchmarkAction = "run_missing_stages" | "reexecute";
export type BenchmarkJobState = "accepted" | "archiving" | "loading_model" | "generating" | "generation_completed" | "executing" | "calculating_metrics" | "completed" | "failed" | "interrupted";

export interface ArtifactSnapshot {
  relative_path: string;
  exists: boolean;
  size: number | null;
  mtime_ns: number | null;
  sha256: string | null;
}

export interface MetricValue {
  value: number | null;
  available: boolean;
  denominator: number;
  numerator?: number | null;
}

export interface BenchmarkCounts {
  total: number;
  correct: number;
  incorrect_without_error: number;
  errors: number;
  timeouts: number;
}

export interface BenchmarkTimes {
  generation: number;
  execution_ground_truth: number;
  execution_generated: number;
  execution_total: number;
  recorded_total: number;
}

export interface BenchmarkResult {
  metrics: Record<string, MetricValue> | null;
  counts: BenchmarkCounts | null;
  times: BenchmarkTimes | null;
}

export interface ExperimentStatus extends BenchmarkResult {
  configuration: ConfigurationSelection;
  seed: number;
  artifact_state: ArtifactState;
  generation: ArtifactSnapshot;
  execution: ArtifactSnapshot;
  invalid_reason: string | null;
}

export interface BenchmarkJob extends BenchmarkResult {
  job_id: string;
  configuration: ConfigurationSelection;
  seed: number;
  action: BenchmarkAction;
  state: BenchmarkJobState;
  stage: BenchmarkJobState;
  artifact_state: ArtifactState;
  created_at: string;
  updated_at: string;
  history_directory: string | null;
  error: PublicError | null;
}
