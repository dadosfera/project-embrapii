import type { BenchmarkJob, CatalogResponse, ConfigurationSelection, Mode, PublicError, SystemStatus } from "../api/types";

export interface AppState {
  mode: Mode;
  catalog: CatalogResponse | null;
  configuration: ConfigurationSelection | null;
  status: SystemStatus | null;
  loading: boolean;
  error: PublicError | null;
}

export type AppAction =
  | { type: "LOAD_STARTED" }
  | { type: "LOAD_SUCCEEDED"; catalog: CatalogResponse; status: SystemStatus }
  | { type: "LOAD_FAILED"; error: PublicError }
  | { type: "STATUS_UPDATED"; status: SystemStatus }
  | { type: "BENCHMARK_RECOVERED"; job: BenchmarkJob }
  | { type: "SET_MODE"; mode: Mode }
  | { type: "SET_CONFIGURATION"; configuration: ConfigurationSelection };

export const initialAppState: AppState = {
  mode: "chat",
  catalog: null,
  configuration: null,
  status: null,
  loading: true,
  error: null
};
