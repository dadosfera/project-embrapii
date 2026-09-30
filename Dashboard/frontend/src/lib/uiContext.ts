/**
 * Contexto de tela enviado ao chat Autodrive (campo `ui_context` de cada pergunta).
 *
 * Duas fontes, lidas no momento em que o usuário pergunta:
 * 1. Variáveis: cada página publica o que está exibindo com `useUiContext({...})` — seleção, KPIs e as séries dos
 *    gráficos (`visible_data`), já em linhas prontas para o assistente plotar.
 * 2. Trechos de HTML: qualquer elemento marcado com `data-chat-context="rótulo"` tem o texto visível copiado para
 *    `page_text` (título e subtítulo da página entram sempre).
 */
import { useEffect } from "react";

export type UiContext = {
  screen: string;
  description?: string;
  filters?: Record<string, unknown>;
  selection?: Record<string, unknown> | null;
  visible_kpis?: Record<string, unknown>;
  visible_data?: Record<string, unknown>;
};

declare global {
  interface Window {
    __embrapiiUiContext?: UiContext;
  }
}

const MAX_TRECHO = 600;
const MAX_TEXTO_TOTAL = 4000;

export function setUiContext(ctx: UiContext) {
  window.__embrapiiUiContext = ctx;
}

/** Publica o contexto da página enquanto ela estiver montada; `deps` define quando republicar. */
export function useUiContext(ctx: UiContext, deps: unknown[]) {
  useEffect(() => {
    setUiContext(ctx);
    return () => {
      if (window.__embrapiiUiContext === ctx) window.__embrapiiUiContext = undefined;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}

function textoVisivel(el: Element): string {
  const texto = (el as HTMLElement).innerText ?? el.textContent ?? "";
  const limpo = texto.replace(/\s+/g, " ").trim();
  return limpo.length > MAX_TRECHO ? `${limpo.slice(0, MAX_TRECHO - 1)}…` : limpo;
}

/** Trechos de texto da página: h1/subtítulo + elementos com data-chat-context. */
export function collectPageText(root: ParentNode = document): Record<string, string> {
  const trechos: Record<string, string> = {};
  let total = 0;
  const add = (rotulo: string, el: Element | null) => {
    if (!el || total >= MAX_TEXTO_TOTAL) return;
    const texto = textoVisivel(el);
    if (!texto) return;
    let chave = rotulo;
    for (let i = 2; chave in trechos; i++) chave = `${rotulo} (${i})`;
    trechos[chave] = texto.slice(0, MAX_TEXTO_TOTAL - total);
    total += trechos[chave].length;
  };
  add("titulo", root.querySelector("main h1"));
  add("subtitulo", root.querySelector("main header p"));
  root.querySelectorAll("[data-chat-context]").forEach((el) => add(el.getAttribute("data-chat-context") || "trecho", el));
  return trechos;
}

const TELAS: Record<string, string> = {
  "": "Início",
  medicamentos: "Medicamentos",
  compras: "Compras",
  leitos: "Leitos",
  mapa: "Mapa",
  fornecedores: "Fornecedores",
};

/** O que vai em `ui_context`: variáveis da página + trechos do HTML + rota. */
export function getUiContext(appBase: string): Record<string, unknown> {
  const path = window.location.pathname.slice(appBase.length).replace(/^\/+|\/+$/g, "");
  const publicado = window.__embrapiiUiContext;
  return {
    app: "Dashboard EMBRAPII / DATASUS",
    path: `/${path}`,
    screen: TELAS[path.split("/")[0]] ?? path,
    ...(publicado ?? {}),
    page_text: collectPageText(),
    captured_at: new Date().toISOString(),
  };
}
