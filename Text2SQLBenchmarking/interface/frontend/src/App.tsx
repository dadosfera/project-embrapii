import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient, PublicApiError, RequestCancelledError } from "./api/client";
import type { BenchmarkJob, CatalogResponse, ConfigurationSelection, Mode } from "./api/types";
import { AppHeader } from "./components/AppHeader";
import { AppSidebar } from "./components/AppSidebar";
import { ConfigurationPanel } from "./components/ConfigurationPanel";
import { ErrorState } from "./components/ErrorState";
import { LoadingState } from "./components/LoadingState";
import { BenchmarkPlaceholder } from "./features/benchmark/BenchmarkPlaceholder";
import { ChatPlaceholder } from "./features/chat/ChatPlaceholder";
import { normalizeConfiguration } from "./state/appReducer";
import { useAppDispatch, useAppState } from "./state/AppContext";

function normalizeChatConfiguration(
  catalog: CatalogResponse,
  requested: ConfigurationSelection
): ConfigurationSelection {
  const library = catalog.libraries.find((item) => item.id === requested.library && item.availability.chat.available)
    ?? catalog.libraries.find((item) => item.availability.chat.available);
  return library
    ? normalizeConfiguration(catalog, { ...requested, library: library.id })
    : normalizeConfiguration(catalog, requested);
}

function ApplicationShell() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const [sidebarOpen, setSidebarOpen] = useState(() => (
    typeof window.matchMedia === "function" ? window.matchMedia("(min-width: 901px)").matches : true
  ));
  const [chatVisible, setChatVisible] = useState(false);
  const [chatActive, setChatActive] = useState(false);
  const [benchmarkVisible, setBenchmarkVisible] = useState(false);
  const [benchmarkActive, setBenchmarkActive] = useState(false);
  const [benchmarkSeed, setBenchmarkSeed] = useState(42);
  const requestRef = useRef<AbortController | null>(null);
  const benchmarkStatusTimer = useRef<number | null>(null);
  const benchmarkStatusRequest = useRef<AbortController | null>(null);
  const modeConfigurations = useRef<Partial<Record<Mode, ConfigurationSelection>>>({});

  const load = useCallback(() => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    dispatch({ type: "LOAD_STARTED" });
    Promise.all([apiClient.getCatalog(controller.signal), apiClient.getStatus(controller.signal)])
      .then(([catalog, status]) => {
        if (requestRef.current !== controller) return;
        dispatch({ type: "LOAD_SUCCEEDED", catalog, status });
      })
      .catch((error: unknown) => {
        if (error instanceof RequestCancelledError || requestRef.current !== controller) return;
        controller.abort();
        const publicError = error instanceof PublicApiError
          ? { code: error.code, message: error.message, retryable: error.retryable }
          : { code: "INTERNAL_ERROR", message: "Não foi possível carregar a interface.", retryable: false };
        dispatch({ type: "LOAD_FAILED", error: publicError });
      });
    return controller;
  }, [dispatch]);

  useEffect(() => {
    load();
    return () => {
      requestRef.current?.abort();
    };
  }, [load]);

  useEffect(() => {
    if (state.loading || state.error || !state.catalog) return;
    let disposed = false;
    const refreshStatus = () => {
      const controller = new AbortController();
      benchmarkStatusRequest.current = controller;
      apiClient.getStatus(controller.signal).then((status) => {
        if (!disposed && benchmarkStatusRequest.current === controller) {
          dispatch({ type: "STATUS_UPDATED", status });
        }
      }).catch(() => undefined).finally(() => {
        if (benchmarkStatusRequest.current === controller) benchmarkStatusRequest.current = null;
        if (!disposed) benchmarkStatusTimer.current = window.setTimeout(refreshStatus, 500);
      });
    };
    benchmarkStatusTimer.current = window.setTimeout(refreshStatus, 500);
    return () => {
      disposed = true;
      if (benchmarkStatusTimer.current !== null) window.clearTimeout(benchmarkStatusTimer.current);
      benchmarkStatusTimer.current = null;
      benchmarkStatusRequest.current?.abort();
      benchmarkStatusRequest.current = null;
    };
  }, [dispatch, state.catalog, state.error, state.loading]);

  useEffect(() => {
    if (!state.catalog || !state.configuration) return;
    modeConfigurations.current[state.mode] = state.mode === "chat"
      ? normalizeChatConfiguration(state.catalog, state.configuration)
      : state.configuration;
  }, [state.catalog, state.configuration, state.mode]);

  const updateConfiguration = (next: ConfigurationSelection) => {
    if (!state.catalog) return;
    const normalized = state.mode === "chat"
      ? normalizeChatConfiguration(state.catalog, next)
      : normalizeConfiguration(state.catalog, next);
    modeConfigurations.current[state.mode] = normalized;
    dispatch({ type: "SET_CONFIGURATION", configuration: normalized });
  };
  const updateBenchmarkActivity = useCallback((active: boolean) => {
    setBenchmarkActive(active);
  }, []);
  const recoverBenchmark = useCallback((job: BenchmarkJob) => {
    setBenchmarkSeed(job.seed);
    dispatch({ type: "BENCHMARK_RECOVERED", job });
  }, [dispatch]);
  const busy = Boolean(state.status?.is_busy) || chatActive || benchmarkActive;
  const activeBenchmarkJob = state.status?.active_operation === "BENCHMARK" ? state.status.benchmark_job : null;
  const displayedBenchmarkSeed = activeBenchmarkJob?.seed ?? benchmarkSeed;
  if (state.loading) return <LoadingState />;
  if (state.error) return <ErrorState error={state.error} onRetry={() => { load(); }} />;
  if (!state.catalog || !state.configuration) return <ErrorState error={{ code: "INTERNAL_ERROR", message: "O catálogo não foi disponibilizado pela API.", retryable: false }} onRetry={() => { load(); }} />;

  const catalog = state.catalog;
  const currentConfiguration = state.configuration;
  const displayedConfiguration = state.mode === "chat"
    ? normalizeChatConfiguration(catalog, currentConfiguration)
    : currentConfiguration;
  const setMode = (mode: Mode) => {
    if (mode === "benchmark" && state.mode === "chat" && chatVisible) {
      if (!window.confirm("Trocar para Benchmark apagará a conversa atual. Continuar?")) return;
    }
    if (mode === "chat" && state.mode === "benchmark" && benchmarkVisible) {
      if (!window.confirm("Trocar para Chat limpará a visualização atual do Benchmark. Continuar?")) return;
    }
    modeConfigurations.current[state.mode] = displayedConfiguration;
    const remembered = modeConfigurations.current[mode] ?? currentConfiguration;
    const nextConfiguration = mode === "chat"
      ? normalizeChatConfiguration(catalog, remembered)
      : normalizeConfiguration(catalog, remembered);
    modeConfigurations.current[mode] = nextConfiguration;
    dispatch({ type: "SET_CONFIGURATION", configuration: nextConfiguration });
    dispatch({ type: "SET_MODE", mode });
  };

  return (
    <div className="app-shell">
      <AppHeader
        mode={state.mode}
        disabled={busy}
        status={state.status}
        chatActive={chatActive}
        benchmarkActive={benchmarkActive}
        onModeChange={setMode}
      />
      <div className="workspace">
        <AppSidebar open={sidebarOpen} mode={state.mode} onToggle={() => setSidebarOpen((value) => !value)}>
          <ConfigurationPanel
            catalog={state.catalog}
            configuration={displayedConfiguration}
            mode={state.mode}
            seed={displayedBenchmarkSeed}
            disabled={busy}
            onChange={updateConfiguration}
            onSeedChange={setBenchmarkSeed}
          />
        </AppSidebar>
        <main className="main-content">
          {state.mode === "chat" ? (
            <ChatPlaceholder
              configuration={displayedConfiguration}
              catalog={state.catalog}
              onActivityChange={setChatActive}
              onVisibleChange={setChatVisible}
              onOpenConfiguration={() => setSidebarOpen(true)}
            />
          ) : (
            <BenchmarkPlaceholder
              configuration={displayedConfiguration}
              catalog={state.catalog}
              seed={displayedBenchmarkSeed}
              onSeedChange={setBenchmarkSeed}
              activeBenchmarkJob={activeBenchmarkJob}
              onBenchmarkRecovered={recoverBenchmark}
              onActivityChange={updateBenchmarkActivity}
              onVisibleChange={setBenchmarkVisible}
              onOpenConfiguration={() => setSidebarOpen(true)}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default ApplicationShell;
