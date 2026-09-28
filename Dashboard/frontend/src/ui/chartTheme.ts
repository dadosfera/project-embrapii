/** Paletas e presets de gráfico. As cores vêm das variáveis Beast do index.css. */
export const CATEGORICA_VARS = [
  "--beast-primary-500", "--beast-info-700", "--beast-success-600",
  "--beast-warning-700", "--beast-primary-300", "--beast-danger-600",
] as const;

export const SEQUENCIAL_VARS = [
  "--beast-primary-100", "--beast-primary-200", "--beast-primary-400",
  "--beast-primary-600", "--beast-primary-800",
] as const;

const avisados = new Set<string>();

/**
 * Resolve uma variável Beast para uma cor concreta (Recharts/D3 não entendem `var()`).
 * O retorno `var(${nome})` só existe para `window === undefined` (Vitest/jsdom não calcula
 * `@theme`/`:root` de verdade) — no navegador espera-se sempre um valor computado. Se a
 * variável vier vazia lá (token renomeado/removido do index.css), avisa uma vez por nome
 * em vez de falhar silenciosamente com uma cor quebrada no gráfico.
 */
function cssVar(nome: string): string {
  if (typeof window === "undefined") return `var(${nome})`;
  const valor = getComputedStyle(document.documentElement).getPropertyValue(nome).trim();
  if (!valor && !avisados.has(nome)) {
    avisados.add(nome);
    console.warn(`[chartTheme] ${nome} não resolveu para nenhuma cor; confira src/index.css`);
  }
  return valor || `var(${nome})`;
}

/** Cores resolvidas (para Recharts/D3, que não entendem var()). */
export function categorica(): string[] { return CATEGORICA_VARS.map(cssVar); }
export function sequencial(): string[] { return SEQUENCIAL_VARS.map(cssVar); }

export const eixo = {
  stroke: "var(--beast-basic-600)",
  tick: { fill: "var(--beast-basic-800)", fontSize: 12, fontFamily: "var(--font-body)" },
  tickLine: false,
  axisLine: { stroke: "var(--beast-basic-600)" },
} as const;

export const grade = { stroke: "var(--beast-basic-400)", strokeDasharray: "3 3", vertical: false } as const;

export const tooltip = {
  contentStyle: {
    background: "var(--panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)",
    boxShadow: "var(--shadow-card)", fontFamily: "var(--font-body)", fontSize: 13, color: "var(--text)",
  },
  cursor: { fill: "var(--beast-basic-300)" },
} as const;

/** Séries de linha: reta, com marcador (decisão 5). */
export const linha = { type: "linear" as const, strokeWidth: 2, dot: { r: 3 }, activeDot: { r: 5 } };
