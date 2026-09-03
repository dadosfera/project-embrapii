import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { apiClient, PublicApiError, RequestCancelledError } from "../../api/client";
import dadosferaSymbol from "../../assets/dadosfera-symbol.png";
import type { CatalogResponse, ChatJob, ConfigurationSelection, PublicError } from "../../api/types";
import { ConfigurationSummary, getConfigurationLabels } from "../../components/ConfigurationSummary";
import { Icon } from "../../components/Icon";
import { PublicErrorNotice } from "../../components/PublicErrorNotice";

interface Card { question: string; job: ChatJob }

const isActive = (state: ChatJob["state"]) => !["succeeded", "failed", "expired"].includes(state);
const toPublicError = (reason: unknown, fallback: string): PublicError => reason instanceof PublicApiError
  ? { code: reason.code, message: reason.message, retryable: reason.retryable }
  : { code: "INTERNAL_ERROR", message: fallback, retryable: false };

const stateLabels: Record<ChatJob["state"], string> = {
  accepted: "Preparando consulta...",
  loading_model: "Preparando modelo e recursos...",
  generating: "Gerando SQL...",
  validating_sql: "Validando consulta...",
  executing: "Executando consulta...",
  succeeded: "Concluída",
  failed: "Não concluída",
  expired: "Resultado expirado"
};

function TechnicalDetails({ job, catalog }: { job: ChatJob; catalog?: CatalogResponse }) {
  const labels = getConfigurationLabels(job.configuration, catalog);
  const [copied, setCopied] = useState(false);
  const copyTimer = useRef<number | null>(null);

  useEffect(() => () => {
    if (copyTimer.current !== null) window.clearTimeout(copyTimer.current);
  }, []);

  const copySql = async () => {
    if (!navigator.clipboard || !job.sql) return;
    try {
      await navigator.clipboard.writeText(job.sql);
      setCopied(true);
      if (copyTimer.current !== null) window.clearTimeout(copyTimer.current);
      copyTimer.current = window.setTimeout(() => setCopied(false), 1_800);
    } catch {
      setCopied(false);
    }
  };

  return (
    <details className="technical-details">
      <summary>Detalhes técnicos</summary>
      <div className="technical-details-body">
        <dl className="technical-metadata">
          <div><dt>Base de dados</dt><dd>{labels.database}</dd></div>
          <div><dt>Biblioteca</dt><dd>{labels.library}</dd></div>
          <div><dt>Modelo</dt><dd>{labels.model}</dd></div>
          <div><dt>Contexto</dt><dd>{labels.context}</dd></div>
          {job.generationTimeSeconds !== null && <div><dt>Tempo de geração</dt><dd>{job.generationTimeSeconds} s</dd></div>}
          {job.executionTimeSeconds !== null && <div><dt>Tempo de execução</dt><dd>{job.executionTimeSeconds} s</dd></div>}
          <div><dt>{isActive(job.state) ? "Estado" : "Estado final"}</dt><dd>{stateLabels[job.state]}</dd></div>
        </dl>

        {job.sql && (
          <details className="sql-details">
            <summary><Icon name="code" size={17} />Mostrar SQL</summary>
            <div className="sql-block">
              <button type="button" className="copy-sql" onClick={() => { void copySql(); }}>
                <Icon name="copy" size={16} /><span aria-live="polite">{copied ? "SQL copiada" : "Copiar SQL"}</span>
              </button>
              <pre><code>{job.sql}</code></pre>
            </div>
          </details>
        )}
      </div>
    </details>
  );
}

interface Props {
  configuration: ConfigurationSelection;
  catalog?: CatalogResponse;
  onActivityChange: (value: boolean) => void;
  onVisibleChange: (value: boolean) => void;
  onOpenConfiguration?: () => void;
}

const noop = () => undefined;

export function ChatPlaceholder({ configuration, catalog, onActivityChange, onVisibleChange, onOpenConfiguration = noop }: Props) {
  const [question, setQuestion] = useState("");
  const [cards, setCards] = useState<Card[]>([]);
  const [error, setError] = useState<PublicError | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [actionsOpen, setActionsOpen] = useState(false);
  const mounted = useRef(true);
  const submittingRef = useRef(false);
  const attempt = useRef(0);
  const request = useRef<AbortController | null>(null);
  const timer = useRef<number | null>(null);
  const editor = useRef<HTMLTextAreaElement>(null);

  const stop = () => {
    request.current?.abort();
    request.current = null;
    if (timer.current !== null) window.clearTimeout(timer.current);
    timer.current = null;
  };

  useEffect(() => () => {
    mounted.current = false;
    stop();
    onActivityChange(false);
    onVisibleChange(false);
  }, [onActivityChange, onVisibleChange]);

  useEffect(() => {
    const visible = Boolean(question || cards.length || error);
    onVisibleChange(visible);
    onActivityChange(submitting || cards.some((card) => isActive(card.job.state)));
    const unload = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    if (visible) window.addEventListener("beforeunload", unload);
    return () => window.removeEventListener("beforeunload", unload);
  }, [question, cards, error, submitting, onActivityChange, onVisibleChange]);

  useEffect(() => {
    const node = editor.current;
    if (!node) return;
    node.style.height = "auto";
    node.style.height = `${Math.min(node.scrollHeight, 132)}px`;
  }, [question, cards.length]);

  const poll = (jobId: string, token: number) => {
    if (!mounted.current || token !== attempt.current || request.current) return;
    const controller = new AbortController();
    request.current = controller;
    apiClient.getChat(jobId, controller.signal).then(({ job }) => {
      if (!mounted.current || token !== attempt.current) return;
      setCards((all) => all.map((card) => card.job.job_id === jobId ? { ...card, job } : card));
      if (isActive(job.state)) timer.current = window.setTimeout(() => poll(jobId, token), 500);
    }).catch((reason) => {
      if (!mounted.current || token !== attempt.current || reason instanceof RequestCancelledError) return;
      const received = toPublicError(reason, "Não foi possível acompanhar a operação.");
      const safe = received.code === "JOB_NOT_FOUND"
        ? { code: "JOB_NOT_FOUND", message: "O resultado do Chat expirou ou o servidor foi reiniciado.", retryable: true }
        : received;
      setCards((all) => all.map((card) => card.job.job_id === jobId
        ? { ...card, job: { ...card.job, state: "failed", error: safe } }
        : card));
    }).finally(() => {
      if (request.current === controller) request.current = null;
    });
  };

  const submit = async () => {
    if (!question.trim() || submittingRef.current || cards.some((card) => isActive(card.job.state))) return;
    submittingRef.current = true;
    onActivityChange(true);
    setSubmitting(true);
    setError(null);
    const token = ++attempt.current;
    const controller = new AbortController();
    request.current = controller;
    try {
      const response = await apiClient.createChat(question.trim(), configuration, controller.signal);
      if (!mounted.current || token !== attempt.current) return;
      setCards((all) => [...all, { question: question.trim(), job: response.snapshot }]);
      setQuestion("");
      request.current = null;
      poll(response.job_id, token);
    } catch (reason) {
      if (mounted.current && token === attempt.current && !(reason instanceof RequestCancelledError)) {
        setError(toPublicError(reason, "Não foi possível iniciar a operação."));
      }
    } finally {
      if (request.current === controller) request.current = null;
      if (mounted.current && token === attempt.current) {
        submittingRef.current = false;
        setSubmitting(false);
      }
    }
  };

  const prepareQuestion = (value: string) => {
    setQuestion(value);
    window.requestAnimationFrame(() => editor.current?.focus());
  };
  const active = submitting || cards.some((card) => isActive(card.job.state));
  const databaseName = getConfigurationLabels(configuration, catalog).database;

  const handleComposerKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void submit();
    }
  };

  const clearConversation = () => {
    if (active) return;
    ++attempt.current;
    stop();
    setCards([]);
    setQuestion("");
    setError(null);
    setActionsOpen(false);
  };

  const composer = (
    <div className="composer-shell">
      <label className="sr-only" htmlFor="chat-question">Pergunta independente</label>
      <textarea
        ref={editor}
        id="chat-question"
        value={question}
        rows={1}
        placeholder={`Pergunte sobre ${databaseName}`}
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={handleComposerKeyDown}
        disabled={active}
      />
      <button type="button" className="send-button" onClick={() => { void submit(); }} disabled={!question.trim() || active} aria-label="Enviar pergunta">
        <Icon name="send" size={19} />
      </button>
      <ConfigurationSummary configuration={configuration} catalog={catalog} onOpen={onOpenConfiguration} />
    </div>
  );

  return (
    <section className={`chat-workspace ${cards.length ? "has-history" : "is-empty"}`} aria-labelledby="chat-title">
      <h2 className="sr-only" id="chat-title">Chat SQL</h2>

      <div className="chat-menu" onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setActionsOpen(false);
      }}>
        <button type="button" className="icon-button chat-menu-trigger" aria-label="Mais ações da conversa" aria-haspopup="menu" aria-expanded={actionsOpen} onClick={() => setActionsOpen((open) => !open)}>
          <Icon name="more" />
        </button>
        {actionsOpen && (
          <div className="chat-menu-popover" role="menu">
            <button type="button" role="menuitem" disabled={active} onClick={clearConversation}>Limpar conversa</button>
          </div>
        )}
      </div>

      {cards.length === 0 ? (
        <div className="chat-empty-state">
          <div className="chat-introduction">
            <h3>O que gostaria de saber sobre a base {databaseName}?</h3>
          </div>
          {error && <PublicErrorNotice error={error} title="Não foi possível iniciar a pergunta" onRetry={() => setError(null)} retryLabel="Revisar e tentar manualmente" />}
          {submitting && <p className="query-status" role="status"><span className="query-loader" aria-hidden="true" />Preparando consulta...</p>}
          {composer}
        </div>
      ) : (
        <>
          <div className="chat-transcript" aria-live="polite">
            <div className="chat-thread">
              {cards.map((card) => (
                <article className="chat-exchange" key={card.job.job_id}>
                  <div className="user-message"><p>{card.question}</p></div>
                  <div className="assistant-message">
                    <div className="assistant-avatar" aria-hidden="true"><img src={dadosferaSymbol} alt="" /></div>
                    <div className="assistant-content">
                      {isActive(card.job.state) && (
                        <p className="query-status" role="status"><span className="query-loader" aria-hidden="true" />{stateLabels[card.job.state]}</p>
                      )}
                      {card.job.state === "expired" && <p className="empty-result">O resultado desta consulta expirou.</p>}
                      {card.job.error && (
                        <PublicErrorNotice
                          error={card.job.error}
                          title="A pergunta não foi concluída"
                          onRetry={() => prepareQuestion(card.question)}
                          retryLabel="Tentar novamente"
                        />
                      )}
                      {card.job.state === "failed" && card.job.error && !card.job.error.retryable && (
                        <button type="button" className="secondary-button" onClick={() => prepareQuestion(card.question)}>Editar pergunta</button>
                      )}
                      {card.job.state === "succeeded" && (
                        <>
                          {card.job.rows?.length === 0 ? <p className="empty-result">Resultado vazio.</p> : (
                            <div className="results-scroll">
                              <table>
                                <caption>Resultado da consulta</caption>
                                <thead><tr>{card.job.columns?.map((column) => <th scope="col" key={column}>{column}</th>)}</tr></thead>
                                <tbody>{card.job.rows?.map((row, index) => <tr key={index}>{row.map((value, cell) => <td key={cell}>{String(value ?? "")}</td>)}</tr>)}</tbody>
                              </table>
                            </div>
                          )}
                          {card.job.truncated && <p className="result-note">Resultado truncado em 200 linhas.</p>}
                        </>
                      )}
                      <TechnicalDetails job={card.job} catalog={catalog} />
                    </div>
                  </div>
                </article>
              ))}
              {error && <PublicErrorNotice error={error} title="Não foi possível iniciar a pergunta" onRetry={() => setError(null)} retryLabel="Revisar e tentar manualmente" />}
            </div>
          </div>
          <div className="composer-dock">{composer}</div>
        </>
      )}
    </section>
  );
}
