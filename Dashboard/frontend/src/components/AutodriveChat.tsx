import { useEffect } from "react";

import { APP_BASE, apiUrl } from "../lib/base";
import { getUiContext } from "../lib/uiContext";

/**
 * Widget AutoDrive Chatbot (https://autodrive-standalone.stg.dadosfera.ai/help/how-to/chatbot).
 *
 * Carrega o bundle UMD do Autodrive STG, pede token ao nosso backend (POST /api/autodrive/chat-token) e fala com a
 * Assistant API pelo proxy same-origin /api/autodrive/proxy. A cada pergunta o widget chama `uiContextProvider`,
 * que devolve o contexto da tela (lib/uiContext.ts) e chega ao assistente como `ui_context`.
 * Assistente e KB vêm de GET /api/autodrive/config (variáveis do serviço); sem config o chat não aparece.
 */

type ChatConfig = {
  enabled: boolean;
  widget_host: string;
  client: string;
  environment: string;
  dataset_id: string;
  assistant_id: string;
  title: string;
};

declare global {
  interface Window {
    AutoDriveChat?: { init: (config: Record<string, unknown>) => unknown };
    AutoDriveChatConfig?: Record<string, unknown>;
    __autodriveChatMounted?: boolean;
  }
}

const USER_ID = "embrapii-demo-user";

/** Correções de layout do widget (mesmas do Porto): o :host fixo herda min-height:100% e o composer estoura a largura. */
function injetarCorrecoes(): void {
  const host = document.querySelector("autodrive-chat") as (HTMLElement & { shadowRoot: ShadowRoot | null }) | null;
  const root = host?.shadowRoot;
  if (!root || root.querySelector("#embrapii-ad-chat-fixes")) return;
  const style = document.createElement("style");
  style.id = "embrapii-ad-chat-fixes";
  style.textContent = `
    :host([data-position="bottom-right"]), :host([data-position="bottom-left"]) {
      height: auto !important; min-height: 0 !important; top: auto !important; bottom: 24px !important;
      max-height: calc(100vh - 48px) !important; width: min(480px, calc(100vw - 32px)) !important;
    }
    :host([data-chat-open="true"]) .ad-chat { min-height: 0 !important; height: min(720px, calc(100vh - 170px)) !important; max-height: calc(100vh - 170px) !important; }
    .ad-chat__shell { height: auto !important; min-height: 0 !important; max-width: 100% !important; overflow: visible !important; }
    .ad-chat, .ad-chat__content, .ad-chat__composer, .ad-chat__form, .ad-chat__starter-tray, .ad-chat__starter-list {
      width: 100% !important; max-width: 100% !important; min-width: 0 !important; box-sizing: border-box !important;
    }
    .ad-chat__composer { grid-template-columns: minmax(0, 1fr) !important; }
    .ad-chat__starter-list { flex-wrap: wrap !important; overflow-x: auto !important; }
    .ad-chat__starter-button { max-width: 100% !important; white-space: normal !important; }
    .ad-chat__input { min-width: 0 !important; }
  `;
  root.appendChild(style);
  // o widget acrescenta <style> depois de montar; o nosso precisa ser o último para as regras !important vencerem
  new MutationObserver(() => {
    if (root.lastElementChild !== style) root.appendChild(style);
  }).observe(root, { childList: true });
}

function montar(cfg: ChatConfig) {
  const container = document.createElement("div");
  container.id = "autodrive-chat";
  document.body.appendChild(container);

  const config = {
    container: "#autodrive-chat",
    client: cfg.client,
    apiProfile: "assistant",
    datasetId: cfg.dataset_id,
    assistantId: cfg.assistant_id,
    environment: cfg.environment,
    // o widget exige URL absoluta
    autodriveUrl: `${window.location.origin}${apiUrl("/api/autodrive/proxy")}`,
    tokenEndpoint: apiUrl("/api/autodrive/chat-token"),
    locale: "pt-BR",
    externalUserId: USER_ID,
    title: cfg.title,
    eyebrow: "Autodrive · dados do SUS",
    placeholder: "Pergunte sobre o que está na tela, compras, estoque ou leitos…",
    theme: {
      position: "bottom-right",
      primaryColor: "#28638f",
      accentColor: "#087f8c",
      launcherLabel: "Analista DATASUS",
    },
    uiContextProvider: () => getUiContext(APP_BASE),
    // user_context também força o caminho do assistente que injeta o contexto no prompt
    userContextProvider: () => ({ user_id: USER_ID, tenant_id: "dadosferademo", role: "analista de saúde pública (demo)", locale: "pt-BR" }),
    onError: (error: unknown) => console.error("[autodrive-chat]", error),
  };
  window.AutoDriveChatConfig = config;

  let tentativas = 0;
  const timer = window.setInterval(() => {
    injetarCorrecoes();
    if (++tentativas > 240) window.clearInterval(timer);
  }, 250);

  if (window.AutoDriveChat) {
    window.AutoDriveChat.init(config);
    return;
  }
  // o bundle se inicializa sozinho a partir de window.AutoDriveChatConfig
  const script = document.createElement("script");
  script.src = `${cfg.widget_host.replace(/\/$/, "")}/chatbot/autodrive-chatbot.umd.cjs`;
  script.async = true;
  script.onerror = () => console.error("[autodrive-chat] não foi possível carregar o widget", script.src);
  document.head.appendChild(script);
}

export function AutodriveChat() {
  useEffect(() => {
    if (window.__autodriveChatMounted) return;
    window.__autodriveChatMounted = true;
    fetch(apiUrl("/api/autodrive/config"))
      .then((r) => (r.ok ? (r.json() as Promise<ChatConfig>) : null))
      .then((cfg) => {
        if (cfg?.enabled) montar(cfg);
      })
      .catch((error) => console.warn("[autodrive-chat] sem configuração", error));
  }, []);

  return null;
}
