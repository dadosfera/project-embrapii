# Dashboard DATASUS: visual Beast (subprojeto A) — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deixar o front do Dashboard na identidade Beast (tokens, Quicksand, shell com logo, componentes, estados, números, tema de gráficos), com acessibilidade AA e code-split, sem mudar layout nem fluxo das páginas.

**Architecture:** Tokens Beast em três camadas de variáveis CSS (brutos → semânticos → ponte Tailwind), que repintam as classes existentes sem editá-las. Primitivas shadcn/ui estilizadas só com esses tokens, mais componentes próprios em `src/ui/`. Adoção página a página, com o smoke Playwright rodando depois de cada uma.

**Tech Stack:** React 19, Vite 7, Tailwind 4 (`@tailwindcss/vite`), shadcn/ui (Radix, cmdk), eva-icons, Recharts 3, D3, Vitest + Testing Library, Playwright + `@axe-core/playwright`.

**Spec:** `docs/superpowers/specs/2026-09-25-dashboard-beast-visual-design.md`.

---

## Convenções

- **Onde trabalhar: worktree isolada** (decisão de 25/09). O checkout principal tem a integração do chat Autodrive ainda sem commit, e ela não pode ser tocada. Task 0 cria `/Users/allansene/Repos/dadosfera/project-embrapii-beast`, branch `feat/dashboard-beast`, a partir de `feat/dadosfera-dataapp`. Todos os caminhos abaixo são relativos a `project-embrapii-beast/Dashboard/`.
- **Registries:** npm usa sempre `--registry=https://registry.npmjs.org/`. O CodeArtifact global está com credencial expirada.
- **Backend:** não muda. Para o smoke, sobe o backend da worktree com o Python do venv principal: `../../project-embrapii/Dashboard/.venv/bin/python -m uvicorn backend.main:app --port 8000`, com `DB_ENGINE=snowflake` e o `.env` copiado na Task 0. Nunca `DB_ENGINE=postgres`: o Postgres da UFMG é compartilhado.
- **Smoke:** `cd frontend && npm run build`, backend de pé, `npx playwright test` (9 testes). Passada com prefixo: backend com `APP_BASE_PATH=/pbp-test_8000` e `npm run e2e:prefix`. Os dois são o critério de "não quebrou" depois de cada página.
- **Commits:** um por task, mensagens em português. Push só na Task 18.

## Mapa de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `frontend/src/index.css` | Tokens Beast (1.1), semânticos (1.2), ponte `@theme inline` (1.3), base tipográfica |
| `frontend/src/theme.ts` | **Removido** (tema escuro sai) |
| `frontend/src/lib/utils.ts` | `cn()` do shadcn |
| `frontend/components.json` | Config do shadcn |
| `frontend/src/components/ui/*.tsx` | Primitivas shadcn |
| `frontend/src/ui/format.ts` | Formatadores pt-BR |
| `frontend/src/ui/chartTheme.ts` | Paletas e presets de gráfico |
| `frontend/src/ui/contrast.ts` | Cálculo de contraste WCAG (testes e paleta) |
| `frontend/src/ui/Icon.tsx`, `frontend/src/ui/icons.ts` | Ícones Eva usados no app |
| `frontend/src/ui/AppShell.tsx` | Header, navegação, menu mobile (substitui `components/Layout.tsx`) |
| `frontend/src/ui/PageHeader.tsx`, `KpiCard.tsx`, `EmptyState.tsx`, `ErrorState.tsx`, `ChartFrame.tsx` | Componentes de página |
| `frontend/src/components/DataTable.tsx` | Tabela TanStack reestilizada |
| `frontend/src/pages/*.tsx` | Adoção |
| `frontend/src/App.tsx` | Rotas com `React.lazy` |
| `frontend/scripts/check-bundle.mjs`, `frontend/scripts/check-tokens.mjs` | Guardas de bundle e de cor |
| `frontend/e2e/a11y.spec.ts` | axe nas 6 páginas |
| `frontend/public/logos/DF-LogoHRZ.svg` | Logo oficial |

---

### Task 0: Worktree e ambiente

**Files:** nenhum no repo.

- [ ] **Step 1: Criar a worktree**

```bash
cd /Users/allansene/Repos/dadosfera/project-embrapii
git fetch -q origin
git worktree add -b feat/dashboard-beast ../project-embrapii-beast origin/feat/dadosfera-dataapp
cd ../project-embrapii-beast && git log --oneline -1
```
Expected: HEAD em `b31e942` ou posterior (o spec do A).

- [ ] **Step 2: `.env` e dependências**

```bash
cp /Users/allansene/Repos/dadosfera/project-embrapii/Dashboard/.env Dashboard/.env
git -C Dashboard check-ignore -v .env   # deve mostrar a regra do .gitignore
cd Dashboard/frontend && npm ci --registry=https://registry.npmjs.org/
```

- [ ] **Step 3: Linha de base verde**

Suba o backend conforme as Convenções e rode `npm run build && npx playwright test`.
Expected: `9 passed`. Se falhar aqui, pare e reporte: a base já estaria quebrada antes de qualquer mudança.

---

### Task 1: Vitest e `format.ts`

**Files:** Modify `frontend/package.json`, `frontend/vite.config.ts`. Create `frontend/src/ui/format.ts`, `frontend/src/ui/format.test.ts`, `frontend/src/test/setup.ts`.

- [ ] **Step 1: Dependências de teste**

```bash
npm i -D vitest@^3 jsdom@^25 @testing-library/react@^16 @testing-library/jest-dom@^6 --registry=https://registry.npmjs.org/
```

Em `package.json`, acrescente `"test": "vitest run"` nos scripts. Em `vite.config.ts`, acrescente o bloco `test` (import `defineConfig` de `vitest/config` no lugar de `vite`):

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss()],
  server: { port: 5173 },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
```

`src/test/setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 2: Teste que falha**

`src/ui/format.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { data, moedaCompacta, moedaExata, numeroCompacto, numeroExato, SEM_DADO } from "./format";

const n = (s: string) => s.replace(/ /g, " ");

describe("format", () => {
  it("moeda compacta em pt-BR", () => {
    expect(n(moedaCompacta(50_923_000_000))).toBe("R$ 50,9 bi");
    expect(n(moedaCompacta(1_250_000))).toBe("R$ 1,3 mi");
    expect(n(moedaCompacta(980))).toBe("R$ 980");
  });
  it("número compacto", () => {
    expect(n(numeroCompacto(1_590_225))).toBe("1,6 mi");
    expect(n(numeroCompacto(1_500))).toBe("1,5 mil");
    expect(numeroCompacto(950)).toBe("950");
  });
  it("valores exatos", () => {
    expect(n(moedaExata(1234.5))).toBe("R$ 1.234,50");
    expect(numeroExato(1_590_225)).toBe("1.590.225");
  });
  it("nulo vira 'sem dado', zero continua zero", () => {
    expect(moedaCompacta(null)).toBe(SEM_DADO);
    expect(numeroExato(undefined)).toBe(SEM_DADO);
    expect(numeroCompacto(0)).toBe("0");
  });
  it("data sem deslocar fuso", () => {
    expect(data("2021-01-01")).toBe("01/01/2021");
    expect(data("2021-01-01T00:00:00+00:00")).toBe("01/01/2021");
    expect(data(null)).toBe(SEM_DADO);
  });
});
```

Run: `npx vitest run src/ui/format.test.ts`
Expected: FAIL (módulo `./format` não existe).

- [ ] **Step 3: Implementar**

`src/ui/format.ts`:

```ts
export const SEM_DADO = "sem dado";

type Num = number | null | undefined;

const compacto = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const moedaCompactaFmt = new Intl.NumberFormat("pt-BR", {
  style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1,
});
const moedaExataFmt = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const inteiro = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });

function vazio(v: Num): v is null | undefined {
  return v === null || v === undefined || Number.isNaN(v);
}

export function moedaCompacta(v: Num): string {
  return vazio(v) ? SEM_DADO : moedaCompactaFmt.format(v);
}
export function numeroCompacto(v: Num): string {
  return vazio(v) ? SEM_DADO : compacto.format(v);
}
export function moedaExata(v: Num): string {
  return vazio(v) ? SEM_DADO : moedaExataFmt.format(v);
}
export function numeroExato(v: Num): string {
  return vazio(v) ? SEM_DADO : inteiro.format(v);
}
/** "AAAA-MM-DD" (com ou sem hora) → "DD/MM/AAAA", sem passar por Date para não deslocar o fuso. */
export function data(v: string | null | undefined): string {
  if (!v) return SEM_DADO;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(v);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : v;
}
```

- [ ] **Step 4: Verde**

Run: `npx vitest run src/ui/format.test.ts`
Expected: `5 passed`. Se um caso compacto falhar por diferença do ICU do Node (ex.: "R$ 51 bi"), ajuste `maximumFractionDigits`/`minimumFractionDigits` para produzir exatamente o esperado. **Não mude o esperado.**

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.ts frontend/src/test frontend/src/ui/format.ts frontend/src/ui/format.test.ts
git commit -m "feat(dashboard): formatadores pt-BR e vitest"
```

---

### Task 2: Tokens Beast, Quicksand e fim do tema escuro

**Files:** Modify `frontend/src/index.css`, `frontend/src/main.tsx`, `frontend/src/components/Layout.tsx`, `frontend/index.html`, `frontend/package.json`. Delete `frontend/src/theme.ts`. Create `frontend/scripts/check-tokens.mjs`.

- [ ] **Step 1: Guarda de cor (teste que falha)**

`scripts/check-tokens.mjs`:

```js
// Falha se houver cor hex fora da camada de tokens Beast do index.css.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const HEX = /#[0-9a-fA-F]{3,8}\b/g;
const erros = [];

function walk(dir) {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (/\.(ts|tsx)$/.test(f) && !/\.test\.tsx?$/.test(f)) {
      const m = readFileSync(p, "utf8").match(HEX);
      if (m) erros.push(`${p}: ${[...new Set(m)].join(", ")}`);
    }
  }
}
walk("src");

const css = readFileSync("src/index.css", "utf8");
const ini = css.indexOf("/* beast:tokens:start */");
const fim = css.indexOf("/* beast:tokens:end */");
if (ini < 0 || fim < 0) erros.push("src/index.css: marcadores beast:tokens ausentes");
else {
  const fora = (css.slice(0, ini) + css.slice(fim)).match(HEX);
  if (fora) erros.push(`src/index.css fora da camada de tokens: ${[...new Set(fora)].join(", ")}`);
}

if (erros.length) { console.error(erros.join("\n")); process.exit(1); }
console.log("tokens OK");
```

Em `package.json`: `"check:tokens": "node scripts/check-tokens.mjs"`.

Run: `npm run check:tokens`
Expected: FAIL (marcadores ausentes e hex no CSS atual).

- [ ] **Step 2: Fonte**

```bash
npm i @fontsource/quicksand@^5 --registry=https://registry.npmjs.org/
npm uninstall @fontsource/inter @fontsource/space-grotesk @fontsource/jetbrains-mono
```

- [ ] **Step 3: Reescrever o topo do `index.css`**

Troque tudo, do início do arquivo até o fim do bloco `@theme inline { ... }` (os imports de fonte, o `:root` com `light-dark()`, os seletores `[data-theme]` e o `@theme inline`), por:

```css
@import "@fontsource/quicksand/400.css";
@import "@fontsource/quicksand/500.css";
@import "@fontsource/quicksand/600.css";
@import "@fontsource/quicksand/700.css";
@import "tailwindcss";

/* beast:tokens:start
   Fonte: beast/src/framework/theme/styles/themes/_default.scss (commit 25709803). Única camada com hex. */
:root {
  --beast-primary-100: #d1ccec; --beast-primary-200: #a299da; --beast-primary-300: #7466c7;
  --beast-primary-400: #4533b5; --beast-primary-500: #1700a2; --beast-primary-600: #14008a;
  --beast-primary-700: #14008a; --beast-primary-800: #0c0051; --beast-primary-900: #0d003b;
  --beast-success-100: #dbefdc; --beast-success-200: #b8dfb9; --beast-success-300: #94d095;
  --beast-success-400: #70c072; --beast-success-500: #4db04f; --beast-success-600: #419643;
  --beast-success-700: #367b37; --beast-success-800: #275828; --beast-success-900: #173518;
  --beast-info-100: #d8f2fc; --beast-info-200: #b1e5f9; --beast-info-300: #89d9f6;
  --beast-info-400: #3bccf3; --beast-info-500: #3bbff0; --beast-info-600: #32a2cc;
  --beast-info-700: #2986a8; --beast-info-800: #1e6078; --beast-info-900: #123948;
  --beast-warning-100: #ffebcc; --beast-warning-200: #ffd699; --beast-warning-300: #ffc266;
  --beast-warning-400: #ffad33; --beast-warning-500: #ff9800; --beast-warning-600: #d98100;
  --beast-warning-700: #b36a00; --beast-warning-800: #804c00; --beast-warning-900: #4d2e00;
  --beast-danger-100: #fee2e2; --beast-danger-200: #fecaca; --beast-danger-300: #fca5a5;
  --beast-danger-400: #f87171; --beast-danger-500: #ef4444; --beast-danger-600: #dc2626;
  --beast-danger-700: #b91c1c; --beast-danger-800: #991b1b; --beast-danger-900: #7f1d1d;
  --beast-basic-100: #ffffff; --beast-basic-200: #f9f9f9; --beast-basic-300: #f2f2f2;
  --beast-basic-400: #eeeeee; --beast-basic-500: #dfdfdf; --beast-basic-600: #c8c8c8;
  --beast-basic-700: #939393; --beast-basic-800: #5c5c5c; --beast-basic-900: #333333;
  --beast-basic-1000: #222222; --beast-basic-1100: #101426;
}
/* beast:tokens:end */

/* Semânticos: o único vocabulário do código. */
:root {
  color-scheme: light;
  --font-body: "Quicksand", "Open Sans", sans-serif;

  --bg: var(--beast-basic-200);
  --panel: var(--beast-basic-100);
  --subtle: var(--beast-basic-300);
  --border: var(--beast-basic-500);
  --border-strong: var(--beast-basic-600);
  --text: var(--beast-basic-1100);
  --text-muted: var(--beast-basic-800);
  --primary: var(--beast-primary-500);
  --primary-hover: var(--beast-primary-600);
  --primary-soft: var(--beast-primary-100);
  --focus-ring: var(--beast-primary-300);
  --success: var(--beast-success-600);  --success-soft: var(--beast-success-100);
  --warning: var(--beast-warning-700);  --warning-soft: var(--beast-warning-100);
  --danger: var(--beast-danger-600);    --danger-soft: var(--beast-danger-100);
  --info: var(--beast-info-700);        --info-soft: var(--beast-info-100);

  --radius-sm: 4px;
  --radius-md: 8px;
  --shadow-card: 0 1px 2px rgb(16 20 38 / 0.06);
  --duration-fast: 120ms;
  --duration-base: 160ms;
  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);

  font-family: var(--font-body);
  color: var(--text);
  background: var(--bg);
  font-synthesis: none;
  text-rendering: optimizeLegibility;
}

/* Ponte: as classes que as páginas já usam passam a apontar para os semânticos. */
@theme inline {
  --font-sans: var(--font-body);
  --radius-2xl: var(--radius-md);
  --radius-xl: var(--radius-md);
  --radius-lg: var(--radius-md);

  --color-white: var(--panel);
  --color-slate-50: var(--bg);
  --color-slate-100: var(--subtle);
  --color-slate-200: var(--border);
  --color-slate-300: var(--border-strong);
  --color-slate-400: var(--text-muted);
  --color-slate-500: var(--text-muted);
  --color-slate-600: var(--text-muted);
  --color-slate-700: var(--text);
  --color-slate-800: var(--text);
  --color-slate-900: var(--text);

  --color-teal-50: var(--primary-soft);
  --color-teal-100: var(--border);
  --color-teal-200: var(--border);
  --color-teal-600: var(--primary);
  --color-teal-700: var(--primary);
  --color-teal-800: var(--primary-hover);
  --color-teal-900: var(--text);
  --color-cyan-50: var(--subtle);

  --color-amber-50: var(--warning-soft);
  --color-amber-200: var(--warning);
  --color-amber-700: var(--warning);
  --color-amber-900: var(--warning);
  --color-red-50: var(--danger-soft);
  --color-red-200: var(--danger);
  --color-red-800: var(--danger);
  --color-blue-50: var(--subtle);
  --color-blue-200: var(--border);
  --color-blue-800: var(--primary);

  /* Vocabulário novo, para o código novo. */
  --color-primary: var(--primary);
  --color-primary-hover: var(--primary-hover);
  --color-primary-soft: var(--primary-soft);
  --color-muted: var(--text-muted);
  --color-panel: var(--panel);
  --color-surface: var(--bg);
  --color-subtle: var(--subtle);
  --color-line: var(--border);
  --color-success: var(--success);
  --color-warning: var(--warning);
  --color-danger: var(--danger);
  --color-info: var(--info);
}
```

Depois, no resto do arquivo:
- troque as referências a variáveis que deixaram de existir: `--color-brand-blue`, `--color-brand-cyan` e `--cta` viram `--primary`; `--step-1` a `--step-5`, `--editor` e `--focus-ring` antigo viram o semântico mais próximo;
- apague as regras `.theme-toggle` e `.brand-logo-dark`.

Para confirmar que não sobrou nada, rode:

```bash
grep -nE "light-dark|data-theme|--step-|--color-brand|--cta|--editor|brand-logo-dark|theme-toggle" src/index.css
```

Expected: vazio.

- [ ] **Step 4: Remover o tema escuro do código**

- **Arquivo:** `git rm src/theme.ts`.
- **`main.tsx`:** remova `import { initTheme } from "./theme";` e a chamada `initTheme();`.
- **`Layout.tsx`:**
  - remova o import de `../theme`, o `themeMeta`, o `useState` do tema, `cycleTheme` e o `<button className="theme-toggle">`;
  - tire o `<img>` com `brand-logo-dark`;
  - troque `useState` por nada no import se ficar sem uso.

A Task 5 substitui esse componente, mas o build precisa passar agora.

`index.html`:
- `<title>Dados em Saúde · EMBRAPII</title>`
- remova qualquer `<meta name="color-scheme">`.

- [ ] **Step 5: Verde**

Run: `npm run check:tokens && npx tsc -b --noEmit && npm run build`
Expected: `tokens OK`. Se `check:tokens` acusar hex em `.tsx` (a varredura inicial achou `#28638f` e `#087f8c`), troque por `var(--primary)`/`var(--info)` no próprio arquivo.

Depois, o smoke (backend de pé): `npx playwright test`
Expected: `9 passed`.

- [ ] **Step 6: Commit**

```bash
git add -A frontend
git commit -m "feat(dashboard): tokens Beast, Quicksand e fim do tema escuro"
```

---

### Task 3: Contraste e tema de gráficos

**Files:** Create `frontend/src/ui/contrast.ts`, `frontend/src/ui/contrast.test.ts`, `frontend/src/ui/chartTheme.ts`, `frontend/src/ui/chartTheme.test.ts`.

As cores precisam existir em TS para Recharts/D3. Para não repetir hex fora do CSS, o `chartTheme` lê as variáveis CSS em runtime e tem fallback só nos testes.

- [ ] **Step 1: Testes que falham**

`src/ui/contrast.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { contraste } from "./contrast";

describe("contraste WCAG", () => {
  it("preto no branco é 21", () => expect(contraste("rgb(0,0,0)", "rgb(255,255,255)")).toBeCloseTo(21, 0));
  it("mesma cor é 1", () => expect(contraste("rgb(23,0,162)", "rgb(23,0,162)")).toBeCloseTo(1, 5));
  it("aceita hex", () => expect(contraste("#000000", "#ffffff")).toBeCloseTo(21, 0));
});
```

`src/ui/chartTheme.test.ts` (as cores reais da paleta categórica, em `rgb()`, para validar contra branco e entre si):

```ts
import { describe, expect, it } from "vitest";
import { contraste } from "./contrast";
import { CATEGORICA_VARS, SEQUENCIAL_VARS } from "./chartTheme";

// valores das variáveis Beast (espelho de src/index.css camada 1.1), só para o teste
const BEAST: Record<string, string> = {
  "--beast-primary-500": "rgb(23,0,162)", "--beast-info-700": "rgb(41,134,168)",
  "--beast-success-600": "rgb(65,150,67)", "--beast-warning-700": "rgb(179,106,0)",
  "--beast-primary-300": "rgb(116,102,199)", "--beast-danger-600": "rgb(220,38,38)",
};
const BRANCO = "rgb(255,255,255)";

describe("paleta categórica", () => {
  it("tem 6 cores", () => expect(CATEGORICA_VARS).toHaveLength(6));
  it("cada cor tem contraste >= 3 contra o fundo (marcas gráficas, WCAG 1.4.11)", () => {
    for (const v of CATEGORICA_VARS) expect(contraste(BEAST[v], BRANCO), v).toBeGreaterThanOrEqual(3);
  });
  it("sequencial tem 5 classes", () => expect(SEQUENCIAL_VARS).toHaveLength(5));
});
```

Run: `npx vitest run src/ui`
Expected: FAIL (módulos ausentes).

- [ ] **Step 2: Implementar**

`src/ui/contrast.ts`:

```ts
function rgb(cor: string): [number, number, number] {
  const m = /rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i.exec(cor);
  if (m) return [Number(m[1]), Number(m[2]), Number(m[3])];
  const h = cor.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  return [0, 2, 4].map((i) => parseInt(full.slice(i, i + 2), 16)) as [number, number, number];
}
function luminancia(cor: string): number {
  const [r, g, b] = rgb(cor).map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
/** Razão de contraste WCAG 2.x entre duas cores (rgb() ou hex). */
export function contraste(a: string, b: string): number {
  const [l1, l2] = [luminancia(a), luminancia(b)].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
}
```

`src/ui/chartTheme.ts`:

```ts
/** Paletas e presets de gráfico. As cores vêm das variáveis Beast do index.css. */
export const CATEGORICA_VARS = [
  "--beast-primary-500", "--beast-info-700", "--beast-success-600",
  "--beast-warning-700", "--beast-primary-300", "--beast-danger-600",
] as const;

export const SEQUENCIAL_VARS = [
  "--beast-primary-100", "--beast-primary-200", "--beast-primary-400",
  "--beast-primary-600", "--beast-primary-800",
] as const;

function cssVar(nome: string): string {
  if (typeof window === "undefined") return `var(${nome})`;
  return getComputedStyle(document.documentElement).getPropertyValue(nome).trim() || `var(${nome})`;
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
```

O spec pede `info-600` e `warning-500`, mas eles não atingem 3:1 contra o fundo branco: `info-600` dá cerca de 2,9 e `warning-500` cerca de 2,2. Os dois foram trocados pela cor mais próxima da mesma escala que passa: `info-700` (cerca de 4,1) e `warning-700` (cerca de 4,2). `warning-600` também não passa (cerca de 2,96). O teste do Step 1 prova as escolhas. Registre a troca no commit.

- [ ] **Step 3: Verde e commit**

Run: `npx vitest run src/ui` → Expected: todos passam.

```bash
git add frontend/src/ui/contrast.ts frontend/src/ui/contrast.test.ts frontend/src/ui/chartTheme.ts frontend/src/ui/chartTheme.test.ts
git commit -m "feat(dashboard): tema de graficos Beast com contraste validado

info-600 e warning-500 trocados por info-700 e warning-700: nao atingiam 3:1 sobre o fundo branco."
```

---

### Task 4: shadcn/ui com tokens Beast

**Files:** Create `frontend/components.json`, `frontend/src/lib/utils.ts`, `frontend/src/components/ui/*`. Modify `frontend/tsconfig.json`, `frontend/tsconfig.app.json`, `frontend/vite.config.ts`, `frontend/src/index.css`.

- [ ] **Step 1: Alias `@`**

Em `tsconfig.json` e `tsconfig.app.json`, dentro de `compilerOptions`:

```json
"baseUrl": ".",
"paths": { "@/*": ["./src/*"] }
```

Em `vite.config.ts`: `import path from "node:path";` e, no objeto, `resolve: { alias: { "@": path.resolve(__dirname, "./src") } },`. Se `__dirname` não existir no ESM, use `fileURLToPath(new URL("./src", import.meta.url))`.

Run: `npm i -D @types/node --registry=https://registry.npmjs.org/ && npx tsc -b --noEmit`
Expected: sem erro.

- [ ] **Step 2: Init e componentes**

```bash
npm_config_registry=https://registry.npmjs.org/ npx shadcn@latest init -y --base-color neutral
npm_config_registry=https://registry.npmjs.org/ npx shadcn@latest add -y button input card tabs select tooltip popover command badge skeleton sheet table
```

O `init` pode acrescentar ao `index.css` um bloco `:root { --background: oklch(...) ... }`, um `.dark { ... }` e um `@theme inline` com `--color-background` etc. **Apague os valores `oklch` e o `.dark`** e deixe as variáveis do shadcn apontando para os semânticos, logo abaixo do bloco de semânticos:

```css
:root {
  --background: var(--bg);
  --foreground: var(--text);
  --card: var(--panel);
  --card-foreground: var(--text);
  --popover: var(--panel);
  --popover-foreground: var(--text);
  --primary-foreground: var(--beast-basic-100);
  --secondary: var(--subtle);
  --secondary-foreground: var(--text);
  --muted: var(--subtle);
  --muted-foreground: var(--text-muted);
  --accent: var(--primary-soft);
  --accent-foreground: var(--primary);
  --destructive: var(--danger);
  --input: var(--border);
  --ring: var(--focus-ring);
  --radius: var(--radius-md);
}
```

O `--primary` e o `--border` já existem nos semânticos com o mesmo nome. Mantenha o `@theme inline` do shadcn (`--color-background: var(--background)` etc.) e **mescle-o** ao `@theme inline` da Task 2, sem duplicar o bloco. Nomes iguais nos dois (`--color-primary`, `--color-muted`) ficam com a definição da Task 2.

Run: `grep -nE "oklch|\.dark" src/index.css` → Expected: vazio.

- [ ] **Step 3: Conferir primitivas**

Run: `npm run check:tokens && npx tsc -b --noEmit && npm run build`
Expected: OK. Se algum componente gerado trouxer classe de cor fixa do Tailwind (`bg-zinc-*`, `text-neutral-*`), troque pela classe semântica equivalente (`bg-panel`, `text-muted`, `border-line`):

```bash
grep -rnE "(zinc|neutral|stone|gray)-[0-9]" src/components/ui
```

Expected no fim: vazio.

- [ ] **Step 4: Commit**

```bash
git add -A frontend
git commit -m "feat(dashboard): primitivas shadcn/ui estilizadas com tokens Beast"
```

---

### Task 5: Ícones Eva e `AppShell`

**Files:** Create `frontend/src/ui/icons.ts`, `frontend/src/ui/Icon.tsx`, `frontend/src/ui/Icon.test.tsx`, `frontend/src/ui/AppShell.tsx`, `frontend/src/ui/AppShell.test.tsx`, `frontend/public/logos/DF-LogoHRZ.svg`. Modify `frontend/src/App.tsx`. Delete `frontend/src/components/Layout.tsx`, `frontend/public/logos/*.png`.

- [ ] **Step 1: Dependência e logo**

```bash
npm i eva-icons@^1.1.3 --registry=https://registry.npmjs.org/
cp /Users/allansene/Repos/dadosfera/ai-cto-assistants/docs/assets/logos/DF-LogoHRZ.svg frontend/public/logos/
ls node_modules/eva-icons/outline/svg | head -3   # confirmar o caminho dos SVGs
```

- [ ] **Step 2: Testes que falham**

`src/ui/Icon.test.tsx`:

```tsx
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Icon } from "./Icon";

describe("Icon", () => {
  it("renderiza svg decorativo por padrão", () => {
    const { container } = render(<Icon name="search" />);
    const el = container.firstElementChild!;
    expect(el.getAttribute("aria-hidden")).toBe("true");
    expect(container.innerHTML).toContain("<svg");
  });
  it("com label vira imagem acessível", () => {
    const { getByRole } = render(<Icon name="search" label="Buscar" />);
    expect(getByRole("img", { name: "Buscar" })).toBeInTheDocument();
  });
});
```

`src/ui/AppShell.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { AppShell } from "./AppShell";

describe("AppShell", () => {
  it("mostra logo, selo do projeto e os 6 destinos", () => {
    render(<MemoryRouter><AppShell><p>conteúdo</p></AppShell></MemoryRouter>);
    expect(screen.getByAltText("Dadosfera")).toBeInTheDocument();
    expect(screen.getByText("Projeto EMBRAPII · DCC/UFMG")).toBeInTheDocument();
    for (const nome of ["Início", "Medicamentos", "Compras", "Leitos", "Mapa", "Fornecedores"]) {
      expect(screen.getAllByRole("link", { name: nome }).length).toBeGreaterThan(0);
    }
    expect(screen.getByText("conteúdo")).toBeInTheDocument();
  });
});
```

Run: `npx vitest run src/ui` → Expected: FAIL (módulos ausentes).

- [ ] **Step 3: `icons.ts` e `Icon.tsx`**

`src/ui/icons.ts` (import explícito de cada SVG usado, para não empacotar os 480 ícones):

```ts
import home from "eva-icons/outline/svg/home-outline.svg?raw";
import droplet from "eva-icons/outline/svg/droplet-outline.svg?raw";
import cart from "eva-icons/outline/svg/shopping-cart-outline.svg?raw";
import activity from "eva-icons/outline/svg/activity-outline.svg?raw";
import map from "eva-icons/outline/svg/map-outline.svg?raw";
import briefcase from "eva-icons/outline/svg/briefcase-outline.svg?raw";
import search from "eva-icons/outline/svg/search-outline.svg?raw";
import menu from "eva-icons/outline/svg/menu-outline.svg?raw";
import close from "eva-icons/outline/svg/close-outline.svg?raw";
import alert from "eva-icons/outline/svg/alert-circle-outline.svg?raw";
import info from "eva-icons/outline/svg/info-outline.svg?raw";
import refresh from "eva-icons/outline/svg/refresh-outline.svg?raw";
import inbox from "eva-icons/outline/svg/inbox-outline.svg?raw";
import calendar from "eva-icons/outline/svg/calendar-outline.svg?raw";
import funnel from "eva-icons/outline/svg/funnel-outline.svg?raw";
import trending from "eva-icons/outline/svg/trending-up-outline.svg?raw";
import arrowDown from "eva-icons/outline/svg/arrow-downward-outline.svg?raw";

export const ICONS = {
  home, droplet, cart, activity, map, briefcase, search, menu, close,
  alert, info, refresh, inbox, calendar, funnel, trending, arrowDown,
} as const;

export type IconName = keyof typeof ICONS;
```

Se o TS reclamar do `?raw`, `vite/client` já declara esse sufixo (está em `types` do `tsconfig.app.json`). Se algum nome não existir no pacote, confira com `ls node_modules/eva-icons/outline/svg | grep <nome>` e troque pelo equivalente mais próximo.

`src/ui/Icon.tsx`:

```tsx
import { ICONS, type IconName } from "./icons";

type Props = { name: IconName; size?: number; label?: string; className?: string };

/** Ícone Eva (outline). Decorativo por padrão; com `label` vira imagem acessível. */
export function Icon({ name, size = 20, label, className }: Props) {
  const svg = ICONS[name].replace("<svg", `<svg width="${size}" height="${size}" fill="currentColor"`);
  return (
    <span
      className={["inline-flex shrink-0", className].filter(Boolean).join(" ")}
      style={{ width: size, height: size }}
      {...(label ? { role: "img", "aria-label": label } : { "aria-hidden": true })}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
```

O `dangerouslySetInnerHTML` é aceitável aqui porque o conteúdo vem de arquivos SVG do pacote, empacotados no build, e nunca de dado do usuário.

- [ ] **Step 4: `AppShell.tsx`**

```tsx
import { type ReactNode, useState } from "react";
import { NavLink } from "react-router";

import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { assetUrl } from "@/lib/base";
import { Icon } from "./Icon";
import type { IconName } from "./icons";

const DESTINOS: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: "/", label: "Início", icon: "home", end: true },
  { to: "/medicamentos", label: "Medicamentos", icon: "droplet" },
  { to: "/compras", label: "Compras", icon: "cart" },
  { to: "/leitos", label: "Leitos", icon: "activity" },
  { to: "/mapa", label: "Mapa", icon: "map" },
  { to: "/fornecedores", label: "Fornecedores", icon: "briefcase" },
];

function linkClass({ isActive }: { isActive: boolean }) {
  return [
    "inline-flex min-h-10 items-center gap-2 rounded-[var(--radius-sm)] px-3 text-sm font-semibold transition-colors",
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]",
    isActive ? "bg-primary-soft text-primary" : "text-muted hover:bg-subtle hover:text-[var(--text)]",
  ].join(" ");
}

function Navegacao({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      {DESTINOS.map((d) => (
        <NavLink key={d.to} to={d.to} end={d.end} className={linkClass} onClick={onNavigate}>
          <Icon name={d.icon} size={18} />
          {d.label}
        </NavLink>
      ))}
    </>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [aberto, setAberto] = useState(false);
  return (
    <div className="min-h-screen bg-surface">
      <header className="sticky top-0 z-20 border-b border-line bg-panel/95 backdrop-blur">
        <div className="mx-auto flex min-h-16 max-w-[1440px] items-center gap-4 px-4 md:px-8">
          <NavLink to="/" className="flex items-center gap-3" aria-label="Dadosfera — Início">
            <img src={assetUrl("logos/DF-LogoHRZ.svg")} alt="Dadosfera" className="h-7 w-auto" />
            <span className="hidden border-l border-line pl-3 text-xs font-semibold text-muted sm:inline">
              Projeto EMBRAPII · DCC/UFMG
            </span>
          </NavLink>

          <nav aria-label="Navegação principal" className="ml-auto hidden items-center gap-1 lg:flex">
            <Navegacao />
          </nav>

          <Sheet open={aberto} onOpenChange={setAberto}>
            <SheetTrigger
              className="ml-auto inline-flex h-10 w-10 items-center justify-center rounded-[var(--radius-sm)] text-[var(--text)] hover:bg-subtle lg:hidden"
              aria-label="Abrir menu"
            >
              <Icon name="menu" size={22} />
            </SheetTrigger>
            <SheetContent side="right" className="w-72 bg-panel">
              <SheetTitle className="px-1 text-sm font-semibold text-muted">Navegação</SheetTitle>
              <nav aria-label="Navegação principal (menu)" className="mt-4 flex flex-col gap-1">
                <Navegacao onNavigate={() => setAberto(false)} />
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </header>
      {children}
    </div>
  );
}
```

O selo aparece no header a partir de `sm`. No teste com jsdom, a classe `hidden` não esconde nada, então o texto está no DOM.

- [ ] **Step 5: Trocar o `Layout` pelo `AppShell`**

- **`App.tsx`:** `import { AppShell } from "./ui/AppShell";` e troque `<Layout>`/`</Layout>` por `<AppShell>`/`</AppShell>`.
- **Remoções:** `git rm src/components/Layout.tsx public/logos/logodadosfera.png public/logos/dadosferabranco.png`.
- **CSS morto:** remova do `index.css` as regras órfãs do Layout antigo (`.app-shell`, `.app-header`, `.brand-mark`, `.brand-logo*`, `.nav-link*`). Confira com `grep -rn "app-header\|nav-link\|brand-" src` fora do CSS, que deve voltar vazio.

- [ ] **Step 6: Verde e commit**

Run: `npx vitest run && npm run check:tokens && npm run build && npx playwright test`
Expected: vitest verde, `tokens OK` e smoke `9 passed`. A 390 px, o menu vira o botão, e o smoke não depende da navegação.

```bash
git add -A frontend
git commit -m "feat(dashboard): AppShell Beast com logo oficial, icones Eva e menu mobile"
```

---

### Task 6: Componentes de página

**Files:** Create in `frontend/src/ui/`: `PageHeader.tsx`, `KpiCard.tsx`, `EmptyState.tsx`, `ErrorState.tsx`, `ChartFrame.tsx`, `components.test.tsx`.

- [ ] **Step 1: Testes que falham**

`src/ui/components.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ApiError } from "@/lib/http";
import { ChartFrame } from "./ChartFrame";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { KpiCard } from "./KpiCard";
import { PageHeader } from "./PageHeader";
import { moedaCompacta } from "./format";

describe("componentes de página", () => {
  it("PageHeader tem h1 e descrição", () => {
    render(<PageHeader icon="cart" title="Compras" description="Compras públicas" />);
    expect(screen.getByRole("heading", { level: 1, name: "Compras" })).toBeInTheDocument();
    expect(screen.getByText("Compras públicas")).toBeInTheDocument();
  });
  it("KpiCard mostra compacto e 'sem dado' para nulo", () => {
    const { rerender } = render(<TooltipProvider><KpiCard label="Valor" value={50_923_000_000} format={moedaCompacta} /></TooltipProvider>);
    expect(screen.getByText(/R\$\s50,9\sbi/)).toBeInTheDocument();
    rerender(<TooltipProvider><KpiCard label="Valor" value={null} format={moedaCompacta} /></TooltipProvider>);
    expect(screen.getByText("sem dado")).toBeInTheDocument();
  });
  it("KpiCard em loading não mostra valor", () => {
    render(<TooltipProvider><KpiCard label="Valor" value={10} format={moedaCompacta} loading /></TooltipProvider>);
    expect(screen.queryByText(/R\$/)).not.toBeInTheDocument();
  });
  it("EmptyState mostra causa e ação", () => {
    render(<EmptyState title="Sem estoque" cause="Nenhuma instituição registrou." action={<button>Ver outro</button>} />);
    expect(screen.getByText("Nenhuma instituição registrou.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ver outro" })).toBeInTheDocument();
  });
  it("ErrorState chama onRetry", () => {
    const onRetry = vi.fn();
    render(<ErrorState error={new ApiError(503, "Banco indisponível")} onRetry={onRetry} />);
    expect(screen.getByText("Banco indisponível")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Tentar de novo" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
  it("ChartFrame tem título e fonte", () => {
    render(<ChartFrame title="Evolução" source="DATASUS"><div>g</div></ChartFrame>);
    expect(screen.getByRole("heading", { name: "Evolução" })).toBeInTheDocument();
    expect(screen.getByText(/DATASUS/)).toBeInTheDocument();
  });
});
```

Run: `npx vitest run src/ui/components.test.tsx` → Expected: FAIL.

- [ ] **Step 2: Implementar**

`src/ui/PageHeader.tsx`:

```tsx
import type { ReactNode } from "react";
import { Icon } from "./Icon";
import type { IconName } from "./icons";

type Props = { icon: IconName; title: string; description?: ReactNode; actions?: ReactNode };

export function PageHeader({ icon, title, description, actions }: Props) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex items-start gap-3">
        <span className="mt-1 inline-flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-primary-soft text-primary">
          <Icon name={icon} size={22} />
        </span>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-[var(--text)] sm:text-3xl">{title}</h1>
          {description ? <p className="mt-1 max-w-3xl text-sm leading-6 text-muted sm:text-base">{description}</p> : null}
        </div>
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </header>
  );
}
```

`src/ui/KpiCard.tsx`:

```tsx
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { SEM_DADO, numeroExato } from "./format";

type Props = {
  label: string;
  value: number | null | undefined;
  format: (v: number | null | undefined) => string;
  exact?: (v: number | null | undefined) => string;
  hint?: string;
  loading?: boolean;
};

export function KpiCard({ label, value, format, exact = numeroExato, hint, loading }: Props) {
  const texto = format(value);
  const vazio = texto === SEM_DADO;
  return (
    <article className="rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-5">
      <p className="text-sm font-medium text-muted">{label}</p>
      {loading ? (
        <Skeleton className="mt-3 h-8 w-32" />
      ) : vazio ? (
        <p className="mt-3 text-2xl font-semibold text-muted">{SEM_DADO}</p>
      ) : (
        <Tooltip>
          <TooltipTrigger asChild>
            <p className="mt-3 w-fit cursor-default text-2xl font-bold tabular-nums text-[var(--text)] sm:text-3xl">{texto}</p>
          </TooltipTrigger>
          <TooltipContent>{exact(value)}</TooltipContent>
        </Tooltip>
      )}
      {hint ? <p className="mt-2 text-xs text-muted">{hint}</p> : null}
    </article>
  );
}
```

O `Tooltip` do shadcn exige `TooltipProvider` acima dele. Nesta task, envolva o `<AppShell>` do `App.tsx` em `<TooltipProvider delayDuration={200}>`, importado de `@/components/ui/tooltip`. O teste do Step 1 já renderiza com o provider.

`src/ui/EmptyState.tsx`:

```tsx
import type { ReactNode } from "react";
import { Icon } from "./Icon";

type Props = { title: string; cause: ReactNode; action?: ReactNode };

export function EmptyState({ title, cause, action }: Props) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-[var(--radius-md)] border border-dashed border-line bg-surface px-6 py-10 text-center">
      <Icon name="inbox" size={28} className="text-muted" />
      <p className="font-semibold text-[var(--text)]">{title}</p>
      <p className="max-w-md text-sm text-muted">{cause}</p>
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}
```

`src/ui/ErrorState.tsx`:

```tsx
import { Button } from "@/components/ui/button";
import { Icon } from "./Icon";

type Props = { error: unknown; onRetry?: () => void };

export function ErrorState({ error, onRetry }: Props) {
  const msg = error instanceof Error ? error.message : "Não foi possível carregar os dados.";
  return (
    <div role="alert" className="flex flex-col items-center gap-2 rounded-[var(--radius-md)] border border-[var(--danger)] bg-[var(--danger-soft)] px-6 py-8 text-center">
      <Icon name="alert" size={28} className="text-[var(--danger)]" />
      <p className="font-semibold text-[var(--text)]">Não foi possível carregar</p>
      <p className="max-w-md text-sm text-muted">{msg}</p>
      {onRetry ? (
        <Button variant="outline" onClick={onRetry} className="mt-2">
          <Icon name="refresh" size={16} /> Tentar de novo
        </Button>
      ) : null}
    </div>
  );
}
```

`src/ui/ChartFrame.tsx`:

```tsx
import type { ReactNode } from "react";

type Props = { title: string; subtitle?: ReactNode; source?: string; legend?: ReactNode; children: ReactNode };

export function ChartFrame({ title, subtitle, source, legend, children }: Props) {
  return (
    <section className="rounded-[var(--radius-md)] border border-line bg-panel p-4 shadow-[var(--shadow-card)] sm:p-5">
      <header className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-[var(--text)]">{title}</h2>
          {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
        </div>
        {legend}
      </header>
      {children}
      {source ? <p className="mt-3 text-xs text-muted">Fonte: {source}</p> : null}
    </section>
  );
}
```

- [ ] **Step 3: Verde e commit**

Run: `npx vitest run && npm run check:tokens && npx tsc -b --noEmit`
Expected: tudo verde.

```bash
git add -A frontend
git commit -m "feat(dashboard): PageHeader, KpiCard, EmptyState, ErrorState e ChartFrame"
```

---

### Task 7: `DataTable` reestilizado

**Files:** Modify `frontend/src/components/DataTable.tsx`. Create `frontend/src/components/DataTable.test.tsx`.

Contrato novo, compatível com as chamadas atuais:
- `ColumnDef.meta?.align: "right"` coloca a coluna à direita com `tabular-nums`;
- `meta?.priority: "low"` esconde a coluna abaixo de 1024 px (classe `hidden lg:table-cell`);
- o vazio usa `EmptyState`, com `emptyMessage` como causa;
- o cabeçalho é `sticky`, e a rolagem horizontal fica num `div` com `overflow-x-auto` dentro do card.

Para o TS aceitar `meta`, crie `src/components/table-meta.d.ts`:

```ts
import "@tanstack/react-table";
declare module "@tanstack/react-table" {
  interface ColumnMeta<TData, TValue> {
    align?: "left" | "right";
    priority?: "high" | "low";
  }
}
```

- [ ] **Step 1: Teste que falha**

```tsx
import { render, screen } from "@testing-library/react";
import type { ColumnDef } from "@tanstack/react-table";
import { describe, expect, it } from "vitest";
import { DataTable } from "./DataTable";

type Linha = { nome: string; valor: number };
const cols: ColumnDef<Linha, unknown>[] = [
  { accessorKey: "nome", header: "Nome" },
  { accessorKey: "valor", header: "Valor", meta: { align: "right" } },
  { accessorKey: "obs", header: "Obs", meta: { priority: "low" } },
];

describe("DataTable", () => {
  it("alinha numérico à direita com tabular-nums", () => {
    render(<DataTable data={[{ nome: "A", valor: 10 }]} columns={cols} />);
    const cel = screen.getByText("10").closest("td")!;
    expect(cel.className).toMatch(/text-right/);
    expect(cel.className).toMatch(/tabular-nums/);
  });
  it("coluna de baixa prioridade é escondida abaixo de lg", () => {
    render(<DataTable data={[{ nome: "A", valor: 10 }]} columns={cols} />);
    expect(screen.getByRole("columnheader", { name: "Obs" }).className).toMatch(/hidden lg:table-cell/);
  });
  it("vazio usa EmptyState com a mensagem", () => {
    render(<DataTable data={[]} columns={cols} emptyMessage="Nada no período." />);
    expect(screen.getByText("Nada no período.")).toBeInTheDocument();
  });
});
```

Run: `npx vitest run src/components/DataTable.test.tsx` → Expected: FAIL.

- [ ] **Step 2: Implementar**

Leia o `DataTable.tsx` atual inteiro. Mantenha paginação, ordenação e `pageSize`, e troque só a marcação:
- `<table>` e as células passam a usar as primitivas `Table`, `TableHeader`, `TableRow`, `TableHead`, `TableBody` e `TableCell` de `@/components/ui/table`;
- cada `TableHead`/`TableCell` recebe `className` calculado por:

```ts
function alinhamento(meta?: { align?: string; priority?: string }) {
  return [
    meta?.align === "right" ? "text-right tabular-nums" : "text-left",
    meta?.priority === "low" ? "hidden lg:table-cell" : "",
  ].join(" ");
}
```

- o `TableHeader` recebe `className="sticky top-0 z-10 bg-panel"`;
- o bloco de vazio vira `<EmptyState title="Sem registros" cause={emptyMessage} />`;
- os botões de paginação viram `Button variant="outline" size="sm"`.

- [ ] **Step 3: Marcar as colunas numéricas nas páginas**

Nas `ColumnDef` de todas as páginas, acrescente `meta: { align: "right" }` nas colunas de valor, quantidade, preço e percentual. Para achar as definições:

```bash
grep -n "accessorKey\|header:" src/pages/*.tsx
```

Colunas secundárias (CNPJ, código, município quando há UF) ganham `meta: { priority: "low" }`.

- [ ] **Step 4: Verde e commit**

Run: `npx vitest run && npm run build && npx playwright test`
Expected: tudo verde, e o smoke `9 passed`.

```bash
git add -A frontend
git commit -m "feat(dashboard): DataTable Beast (numeros a direita, prioridade de coluna, estado vazio)"
```

---

### Tasks 8–13: adoção por página

Cada página segue o mesmo roteiro, com o smoke como critério. Os `<h1>` mantêm o mesmo texto: é isso que o smoke procura.

**Roteiro comum (vale para as Tasks 8–13):**
1. **Cabeçalho:** o bloco do topo (o `<h1>` e o parágrafo logo abaixo) vira `<PageHeader icon=… title=… description=… />`, com o mesmo texto do `<h1>`. Emojis saem.
2. **KPIs:** cada card de KPI da página vira `<KpiCard label value format loading />`, usando `moedaCompacta`/`numeroCompacto` e `exact={moedaExata}` nos valores em reais. Os formatadores locais da página (funções `formatar*`, `numero()` e `Intl.NumberFormat` locais) são trocados pelos de `@/ui/format` e depois apagados. Confira com `grep -n "Intl.NumberFormat\|function formatar" src/pages/<Pagina>.tsx`, que deve voltar vazio no fim.
3. **Gráficos:** cada gráfico Recharts é envolvido em `ChartFrame` (título atual, `source="DATASUS"`) e usa `eixo`, `grade`, `tooltip`, `linha` e `categorica()` de `@/ui/chartTheme`. Cores `stroke`/`fill` fixas saem, e o `type="monotone"` vira `linha.type`.
4. **Estados:** blocos de "carregando" usam `Skeleton`, os de erro usam `<ErrorState error onRetry={recarregar} />`, onde `recarregar` é a função que a página já usa para buscar, e os vazios usam `<EmptyState title cause />` com causa específica ("Nenhuma instituição registrou estoque deste medicamento", "Não há compras no período selecionado"). O nulo nunca aparece como 0.
5. **Controles:** `<select>` vira `Select`, `<input>` vira `Input` (altura mínima 40 px), botões viram `Button` e abas viram `Tabs` do shadcn. O comportamento continua igual: mesmos handlers e mesmos valores.
6. **Guardas:** `npm run check:tokens && npx tsc -b --noEmit && npm run build && npx playwright test` precisam estar verdes antes do commit.

- [ ] **Task 8: Home** (`src/pages/Home.tsx`, `icon="home"`) — roteiro comum, mais:
  - **Texto:** a menção a PostgreSQL passa a dizer "no Snowflake da plataforma Dadosfera".
  - **Card de Fornecedores:** acrescente um 5º card de módulo, com o mesmo formato dos outros 4, `to="/fornecedores"`, ícone `briefcase` e a descrição "Origem dos fornecedores das compras públicas, por UF".
  - **Hero curto:** título, uma frase e os números de cobertura. Só entram números que já saem de endpoint existente, por exemplo o total de UFs de `/api/leitos/ufs` e o intervalo de competências de `/api/leitos/intervalo`. Se a Home não chama API hoje, use estes dois, com `KpiCard` e `loading`.
  - **"Ver módulos":** o link `href="#modulos"` vira `<button onClick={() => document.getElementById("modulos")?.scrollIntoView({ behavior: "smooth" })}>`.
  - Commit: `feat(dashboard): Home Beast (texto Snowflake, card Fornecedores, hero, ancora sem reload)`.
- [ ] **Task 9: Medicamentos** (`src/pages/Medicamentos.tsx`, `icon="droplet"`) — roteiro comum. O campo de busca usa `Input` com `className="h-10"`: a 390 px ele encolhia para 20 px. O fluxo buscar → selecionar → pesquisar continua; o autocomplete é do subprojeto B. Commit: `feat(dashboard): Medicamentos Beast`.
- [ ] **Task 10: Compras** (`src/pages/Compras.tsx`, `icon="cart"`) — roteiro comum. O período padrão não muda: é do subprojeto C. Commit: `feat(dashboard): Compras Beast`.
- [ ] **Task 11: Leitos** (`src/pages/Leitos.tsx`, `icon="activity"`) — roteiro comum, mais:
  - **24 meses:** perto da linha 436, o `730` dias vira 24 meses de calendário. Crie a função pura `inicioHaMeses(fim: Date, meses: number): string`, que devolve `AAAA-MM-DD` do mesmo dia N meses antes, com o dia limitado ao último dia do mês.
  - **Teste da função:** crie `src/pages/leitosDatas.test.ts` com os casos `inicioHaMeses(new Date(2026, 8, 25), 24) === "2024-09-25"` e `inicioHaMeses(new Date(2026, 2, 31), 1) === "2026-02-28"`, rodando antes da implementação (TDD). Coloque a função em `src/pages/leitosDatas.ts` e importe na página.
  - **Séries:** as duas séries do gráfico de evolução usam `categorica()[0]` e `categorica()[1]` (primary × info).
  - Commit: `feat(dashboard): Leitos Beast e periodo padrao de 24 meses`.
- [ ] **Task 12: Mapa** (`src/pages/Mapa.tsx`, `icon="map"`, e `src/components/MapaBrasil.tsx`) — roteiro comum. O `MapaBrasil` troca a escala de cor fixa por `sequencial()`, e a lógica de escala (quantis ou linear) fica como está: o redesenho é do subprojeto C. Commit: `feat(dashboard): Mapa Beast`.
- [ ] **Task 13: Fornecedores** (`src/pages/Fornecedores.tsx`, `icon="briefcase"`) — roteiro comum, mais:
  - **Data local:** perto da linha 66, `new Date().toISOString().slice(0, 10)` vira a data local. Crie `hojeLocal(d = new Date()): string` em `src/ui/format.ts`, com teste em `format.test.ts` rodando antes da implementação: para `new Date(2026, 8, 25, 23, 30)`, o resultado é `"2026-09-25"`. A implementação monta a string com `getFullYear`, `getMonth` e `getDate`.
  - **Tabela:** passa a usar o `DataTable` da Task 7, com rolagem contida no card, sem estourar a 1440 px.
  - Commit: `feat(dashboard): Fornecedores Beast e data local`.

---

### Task 14: Code-split por rota e guarda de bundle

**Files:** Modify `frontend/src/App.tsx`, `frontend/package.json`. Create `frontend/scripts/check-bundle.mjs`.

- [ ] **Step 1: Guarda (falha primeiro)**

`scripts/check-bundle.mjs`:

```js
// Falha se o chunk JS de entrada (referenciado no index.html) passar do limite.
import { readFileSync, statSync } from "node:fs";

const LIMITE = 250 * 1024;
const html = readFileSync("dist/index.html", "utf8");
const src = /<script[^>]+type="module"[^>]+src="\.?\/?([^"]+\.js)"/.exec(html)?.[1];
if (!src) { console.error("entrada JS não encontrada no dist/index.html"); process.exit(1); }
const tam = statSync(`dist/${src}`).size;
console.log(`${src}: ${(tam / 1024).toFixed(1)} kB (limite ${LIMITE / 1024} kB)`);
if (tam > LIMITE) process.exit(1);
```

Em `package.json`: `"check:bundle": "node scripts/check-bundle.mjs"`.

Run: `npm run build && npm run check:bundle`
Expected: FAIL (a entrada tem cerca de 787 kB).

- [ ] **Step 2: `React.lazy`**

`App.tsx`:

```tsx
import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router";

import { TooltipProvider } from "@/components/ui/tooltip";
import { Skeleton } from "@/components/ui/skeleton";
import { AppShell } from "./ui/AppShell";

const Home = lazy(() => import("./pages/Home").then((m) => ({ default: m.Home })));
const Medicamentos = lazy(() => import("./pages/Medicamentos").then((m) => ({ default: m.Medicamentos })));
const Compras = lazy(() => import("./pages/Compras").then((m) => ({ default: m.Compras })));
const Leitos = lazy(() => import("./pages/Leitos").then((m) => ({ default: m.Leitos })));
const Mapa = lazy(() => import("./pages/Mapa").then((m) => ({ default: m.Mapa })));
const Fornecedores = lazy(() => import("./pages/Fornecedores").then((m) => ({ default: m.Fornecedores })));

function Carregando() {
  return (
    <div className="mx-auto max-w-[1440px] space-y-4 px-4 py-8 md:px-8" aria-busy="true" aria-label="Carregando página">
      <Skeleton className="h-10 w-72" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

export default function App() {
  return (
    <TooltipProvider delayDuration={200}>
      <AppShell>
        <Suspense fallback={<Carregando />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/medicamentos" element={<Medicamentos />} />
            <Route path="/compras" element={<Compras />} />
            <Route path="/leitos" element={<Leitos />} />
            <Route path="/mapa" element={<Mapa />} />
            <Route path="/fornecedores" element={<Fornecedores />} />
          </Routes>
        </Suspense>
      </AppShell>
    </TooltipProvider>
  );
}
```

Se algum export não tiver o nome esperado, confira com `grep -n "^export function" src/pages/*.tsx` e ajuste o `.then`. Se o provider já tiver entrado na Task 6, não duplique.

- [ ] **Step 3: Verde e commit**

Run: `npm run build && npm run check:bundle && npx playwright test && npm run e2e:prefix`
Expected: entrada abaixo de 250 kB e smoke `9 passed` nas duas passadas. Na passada com prefixo, o backend sobe com `APP_BASE_PATH=/pbp-test_8000`. O `base: './'` do Vite resolve os chunks lazy pelo `<base href>`, e o listener de prefixo do smoke pega regressão.

Se passar de 250 kB, o Recharts provavelmente está na entrada por algum import do `AppShell`/`App`; confira com `npx vite-bundle-visualizer` ou lendo os imports.

```bash
git add -A frontend
git commit -m "perf(dashboard): code-split por rota; entrada abaixo de 250 kB"
```

---

### Task 15: Acessibilidade (axe)

**Files:** Create `frontend/e2e/a11y.spec.ts`. Modify pages/components as needed.

- [ ] **Step 1: Teste**

```bash
npm i -D @axe-core/playwright@^4 --registry=https://registry.npmjs.org/
```

`e2e/a11y.spec.ts`:

```ts
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const ROTAS = ["", "medicamentos", "compras", "leitos", "mapa", "fornecedores"];

for (const largura of [1440, 390]) {
  for (const rota of ROTAS) {
    test(`axe /${rota} @${largura}px`, async ({ page }) => {
      await page.setViewportSize({ width: largura, height: 900 });
      await page.goto(rota);
      await page.waitForLoadState("networkidle");
      const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
      const graves = r.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
      expect(graves.map((v) => `${v.id}: ${v.nodes.length} nós — ${v.help}`)).toEqual([]);
    });
  }
}
```

Run: `npx playwright test e2e/a11y.spec.ts`
Expected no primeiro run: pode falhar. Leia cada violação.

- [ ] **Step 2: Corrigir até zero serious/critical**

Correções típicas:
- **`color-contrast`:** troque a classe pela semântica de contraste maior. Texto secundário usa `text-muted` (`basic-800` sobre branco dá cerca de 6,9:1); placeholder usa `placeholder:text-[var(--beast-basic-800)]`.
- **`label`:** todo `Input`/`Select` precisa de `<label htmlFor>` ou `aria-label`.
- **`button-name`:** botões só com ícone ganham `aria-label`.
- **`region`/`landmark`:** o conteúdo de cada página fica dentro de `<main>`. Se ainda não houver, o `AppShell` envolve `children` em `<main id="conteudo">`.

**Não** desligue regras do axe. Cada correção vai com o arquivo e a regra no commit.

- [ ] **Step 3: Verde e commit**

Run: `npx playwright test` (smoke + a11y)
Expected: todos passam.

```bash
git add -A frontend
git commit -m "fix(dashboard): acessibilidade AA (axe sem violacoes serious/critical)"
```

---

### Task 16: Antes × depois no report de UX

**Files:** Modify `docs/ux-review/index.html`, add `docs/ux-review/shots/depois-*.png`.

- [ ] **Step 1: Capturar**

Com o backend (Snowflake) de pé e o build novo, rode o `docs/ux-review/capture.ts` gravando com prefixo `depois-` (o prefixo é um parâmetro do script ou variável de ambiente; se não houver, acrescente `const PREFIXO = process.env.SHOT_PREFIX ?? ""`). Larguras: 1440, 1024 e 390.

```bash
cd frontend && SHOT_PREFIX=depois- node ../docs/ux-review/capture.ts
```

- [ ] **Step 2: Seção "Antes × depois"**

Em `docs/ux-review/index.html`, logo depois do resumo, acrescente uma seção com uma linha por página e duas figuras lado a lado: o print antigo em `shots/<pagina>.png` e o novo em `shots/depois-<pagina>.png`. Legenda com as decisões atendidas (1, 2, 3, 4, 5, 9, 15, 16, 18, 20). Use o mesmo estilo de figura já existente no arquivo.

- [ ] **Step 3: Commit**

```bash
git add docs/ux-review
git commit -m "docs(dashboard): antes x depois do visual Beast no report de UX"
```

---

### Task 17: QA, deploy e verificação

**Files:** `deploy/manifest.json`.

- [ ] **Step 1: QA (feito pelo controlador).** O controlador despacha o agente `qa-analyst-frontend` (`/Users/allansene/Repos/dadosfera/ai-cto-assistants/.cursor/agents/qa-analyst-frontend.md`), no modo validação pontual, sobre o app local em Snowflake, a 1440, 1024 e 390 px. Ele entrega checklist de fluxos, bugs com severidade e evidência, console e requests com falha. Achado de severidade alta volta como correção antes do Step 2.

- [ ] **Step 2: Deploy a partir da worktree**

```bash
cd frontend && npm run build && cd ..
DADOSFERA_ENV_FILE=/Users/allansene/Repos/dadosfera/ai-cto-assistants/.env ../../project-embrapii/Dashboard/.venv/bin/python deploy/deploy_service.py --start
DADOSFERA_ENV_FILE=/Users/allansene/Repos/dadosfera/ai-cto-assistants/.env ../../project-embrapii/Dashboard/.venv/bin/python deploy/verify.py
```

Expected:
- `environment unchanged` (o backend não mudou);
- a mesma URL;
- `verify.py` 7/7, com `secret_source=env`.

**Atenção:** o deploy sobe o `backend/` da worktree, que ainda não tem o chat Autodrive. Se o chat já tiver sido publicado a partir do checkout principal nesse meio-tempo, este deploy o tira do ar. Confirme com o controlador antes de rodar.

- [ ] **Step 3: Smoke publicado com SSO**

Siga o `deploy/README.md` (seção Smoke) com `E2E_BASE_URL` = `dataapp_url` do manifest.
Expected: `9 passed`.

- [ ] **Step 4: QA no publicado.** Mesma rodada do Step 1, agora na URL publicada, feita pelo controlador.

- [ ] **Step 5: Commit**

```bash
git add deploy/manifest.json && git commit -m "chore(dashboard): manifest apos deploy do visual Beast"
```

---

### Task 18: Push e integração

- [ ] **Step 1:** `git push -u origin feat/dashboard-beast`.
- [ ] **Step 2: Merge (pelo controlador, com o Allan).** A `feat/dashboard-beast` entra na `feat/dadosfera-dataapp` quando a integração do chat Autodrive estiver commitada. Conflitos esperados:
  - **`Layout.tsx`:** removido aqui e modificado lá. O `AutodriveChat` passa a ser renderizado no `AppShell`.
  - **`Medicamentos.tsx`.**

  O merge resolve os dois, e o smoke e o axe rodam de novo antes do push.
- [ ] **Step 3: Limpeza.** `git worktree remove ../project-embrapii-beast` depois do merge.
