import type { CatalogResponse, ConfigurationSelection } from "../api/types";
import type { AppAction, AppState } from "./types";

export function normalizeConfiguration(
  catalog: CatalogResponse,
  requested: ConfigurationSelection
): ConfigurationSelection {
  const library = catalog.libraries.find((item) => item.id === requested.library) || catalog.libraries[0];
  if (!library) return requested;
  const modelId = library.model_ids.includes(requested.model_id)
    ? requested.model_id
    : library.model_ids[0];
  const context = library.contexts.includes(requested.context)
    ? requested.context
    : library.contexts[0];
  return { ...requested, library: library.id, model_id: modelId, context };
}

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "LOAD_STARTED":
      return { ...state, loading: true, error: null };
    case "LOAD_SUCCEEDED": {
      const recoveredConfiguration = action.status.is_busy
        && action.status.active_operation === "BENCHMARK"
        && action.status.benchmark_job
        ? action.status.benchmark_job.configuration
        : action.catalog.initial_configuration;
      return {
        ...state,
        mode: action.status.is_busy && action.status.active_operation === "BENCHMARK" && action.status.benchmark_job ? "benchmark" : state.mode,
        catalog: action.catalog,
        configuration: normalizeConfiguration(action.catalog, recoveredConfiguration),
        status: action.status,
        loading: false,
        error: null
      };
    }
    case "LOAD_FAILED":
      return { ...state, loading: false, error: action.error };
    case "STATUS_UPDATED": {
      const activeBenchmark = action.status.is_busy
        && action.status.active_operation === "BENCHMARK"
        ? action.status.benchmark_job
        : null;
      return {
        ...state,
        mode: activeBenchmark ? "benchmark" : state.mode,
        configuration: activeBenchmark && state.catalog
          ? normalizeConfiguration(state.catalog, activeBenchmark.configuration)
          : state.configuration,
        status: action.status
      };
    }
    case "BENCHMARK_RECOVERED":
      return {
        ...state,
        mode: "benchmark",
        configuration: state.catalog
          ? normalizeConfiguration(state.catalog, action.job.configuration)
          : action.job.configuration
      };
    case "SET_MODE":
      return { ...state, mode: action.mode };
    case "SET_CONFIGURATION":
      return { ...state, configuration: action.configuration };
    default:
      return state;
  }
}
