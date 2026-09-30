# Dashboard DATASUS: visual Beast (subprojeto A) — design

Data: 25/09/2026 · Autor: Allan Sene · Branch: `feat/dadosfera-dataapp`

## Contexto e decomposição

O data app está no ar no Mod. de Inteligência demo2, lendo do Snowflake, com paridade 47/47 (spec `2026-09-24-dashboard-dataapp-dadosferademo-design.md`). O report de UX (`Dashboard/docs/ux-review/index.html`) levantou 41 achados e 20 decisões. O trabalho seguinte foi dividido em três subprojetos, cada um com spec, plano e execução próprios, nesta ordem:

| Subprojeto | Escopo | Decisões do report |
|---|---|---|
| **A. Visual Beast** (este spec) | Tokens, tipografia, shell, componentes base, estados, números, tema de gráficos, correções pontuais, acessibilidade e code-split | 1, 2, 3, 4, 5, 9, 15, 16 (só os bugs de data), 18, 19, 20 |
| B. Busca | Autocomplete, busca sem acento e agrupamento de CATMAT (composição → item-base → variantes) | 7, 8 |
| C. Páginas e visualizações | Carregar ao abrir, períodos padrão, barras anuais, outliers, mapas, destino da página Mapa, visualizações novas | 6, 10, 11, 12, 13, 14, 16 (períodos), 17 |

O A não muda layout, filtros nem fluxo das páginas, e não mexe no backend.

## Decisões

- Só tema claro. O seletor sistema/claro/escuro e o `light-dark()` saem, como no app.dadosfera.ai, onde o data app aparece embedado.
- Abordagem: tokens Beast em variáveis CSS espelhadas no Tailwind 4, primitivas shadcn/ui estilizadas só com esses tokens e um conjunto pequeno de componentes próprios.
- Direção estética: painel analítico editorial. Fundo claro com respiro, primária Beast só em ação e destaque, hierarquia pela tipografia, uma cor forte por gráfico e animação só no fade de troca de dados.

## 1. Tokens e tema

Arquivo: `Dashboard/frontend/src/index.css`, em três camadas.

**1.1 Tokens Beast brutos.** Copiados de `beast/src/framework/theme/styles/themes/_default.scss` (commit `25709803`, citado em comentário no arquivo):

| Escala | 100 | 300 | 500 | 600 | 800 | 900 |
|---|---|---|---|---|---|---|
| `--beast-primary-*` | `#d1ccec` | `#7466c7` | `#1700a2` | `#14008a` | `#0c0051` | `#0d003b` |
| `--beast-success-*` | `#dbefdc` | `#94d095` | `#4db04f` | `#419643` | `#275828` | `#173518` |
| `--beast-info-*` | `#d8f2fc` | `#89d9f6` | `#3bbff0` | `#32a2cc` | `#1e6078` | `#123948` |
| `--beast-warning-*` | `#ffebcc` | `#ffc266` | `#ff9800` | `#d98100` | `#804c00` | `#4d2e00` |
| `--beast-danger-*` | `#fee2e2` | `#fca5a5` | `#ef4444` | `#dc2626` | `#991b1b` | `#7f1d1d` |

As escalas entram completas (100 a 900); a tabela mostra só uma amostra. `--beast-basic-*`: 100 `#ffffff`, 200 `#f9f9f9`, 300 `#f2f2f2`, 400 `#eeeeee`, 500 `#dfdfdf`, 600 `#c8c8c8`, 700 `#939393`, 800 `#5c5c5c`, 900 `#333333`, 1000 `#222222`, 1100 `#101426`.

**1.2 Semânticos.** São os únicos nomes usados pelo código novo.

| Token | Valor |
|---|---|
| `--bg` | `basic-200` |
| `--panel` | `basic-100` |
| `--subtle` | `basic-300` |
| `--border` | `basic-500` |
| `--text` | `basic-1100` |
| `--text-muted` | `basic-800` |
| `--primary` / `--primary-hover` / `--primary-soft` | `primary-500` / `primary-600` / `primary-100` |
| `--focus-ring` | `primary-300` |
| `--success`, `--warning`, `--danger`, `--info` | a escala 600 de cada, escolhida por contraste AA sobre `--panel`; se a 600 não atingir AA, usa-se a 700 e registra-se a troca no commit |
| `--success-soft` etc. | escala 100 |
| `--radius-sm` / `--radius-md` | `4px` (inputs, botões) / `8px` (cards) |
| `--shadow-card` | `0 1px 2px rgb(16 20 38 / 0.06)` |

**1.3 Ponte Tailwind.** No `@theme inline`:
- **Classes antigas:** as que as páginas já usam passam a apontar para os semânticos (`teal-*` → primary, `slate-*` → basic/text, `amber-*` → warning, `red-*` → danger, `blue-*`/`cyan-*` → primary/subtle). As cerca de 311 classes das páginas mudam de cor sem edição.
- **Aliases novos:** `--color-primary-*`, `--color-basic-*`, `--color-success-*`, `--color-warning-*`, `--color-danger-*`, `--color-info-*`.
- **Variáveis do shadcn:** `--background`, `--foreground`, `--card`, `--primary`, `--primary-foreground`, `--muted`, `--muted-foreground`, `--border`, `--input` e `--ring` apontam para os semânticos.

**1.4 Tipografia.**
- **Fonte única:** Quicksand via `@fontsource/quicksand`, pesos 400, 500, 600 e 700. Saem `@fontsource/inter`, `@fontsource/space-grotesk` e `@fontsource/jetbrains-mono`.
- **Números:** tabelas e KPIs usam `font-variant-numeric: tabular-nums`.
- **Pesos:** títulos 600, números de KPI 700.

**1.5 Tema de gráficos.** Arquivo `src/ui/chartTheme.ts`:
- **Categórica:** 6 cores, na ordem primary-500, info-600, success-600, warning-500, primary-300 e danger-500, validadas com o validador da skill `dataviz` (distinção entre pares e contraste contra `--panel`). Cor que não passar é trocada pela vizinha da mesma escala, e a troca vai registrada no arquivo.
- **Sequencial** (mapas): primary-100 → primary-800, em 5 classes.
- **Presets Recharts:** eixos e grade em `basic-500`/`basic-700`, tooltip em `--panel` com borda `--border`, séries de linha com `type="linear"` e `dot`.
- **Mapa D3:** o `MapaBrasil.tsx` lê a mesma sequencial.

## 2. Componentes

**2.1 Primitivas shadcn/ui** em `src/components/ui/`, geradas pelo CLI do shadcn para Tailwind 4 e estilizadas só com tokens: `button`, `input`, `card`, `tabs`, `select`, `tooltip`, `popover`, `command`, `badge`, `skeleton`, `sheet`, `table`. Dependências novas: Radix (pelas primitivas), `cmdk`, `class-variance-authority`, `clsx`, `tailwind-merge` e `eva-icons`.

**2.2 Componentes próprios** em `src/ui/`:

| Componente | Responsabilidade | Interface |
|---|---|---|
| `AppShell` | Header com `DF-LogoHRZ.svg` oficial (copiado de `ai-cto-assistants/docs/assets/logos/`), selo "Projeto EMBRAPII · DCC/UFMG" e navegação com ícone Eva e estado ativo em `--primary`. Abaixo de 768 px vira botão + `Sheet` | `children` |
| `Icon` | Renderiza um SVG outline do `eva-icons` com `aria-hidden` por padrão | `name`, `size`, `label?` |
| `PageHeader` | Ícone, título (`<h1>`), descrição e espaço para ações | `icon`, `title`, `description?`, `actions?` |
| `KpiCard` | Rótulo, valor compacto e valor exato em tooltip. Estado `loading` usa Skeleton; `null` ou `undefined` mostram "sem dado" | `label`, `value`, `format`, `loading?` |
| `EmptyState` | Ícone, título, causa e próximo passo | `title`, `cause`, `action?` |
| `ErrorState` | Mensagem do `ApiError` e botão "Tentar de novo" | `error`, `onRetry` |
| `DataTable` | TanStack atual reestilizado. Cabeçalho fixo; colunas numéricas à direita com `tabular-nums`; rolagem horizontal dentro do card; colunas com `meta.priority = "low"` escondidas abaixo de 1024 px | a API atual mais `meta.align` e `meta.priority` |
| `ChartFrame` | Título, subtítulo, legenda e nota de fonte ao redor de um gráfico | `title`, `subtitle?`, `source?`, `children` |
| `format.ts` | `moedaCompacta` (R$ 50,9 bi), `numeroCompacto` (1,6 mi), `moedaExata`, `numeroExato`, `data` (dd/mm/aaaa) e `semDado` | funções puras |

O título da aba passa a ser "Dados em Saúde · EMBRAPII".

## 3. Adoção nas páginas e correções

Nas 6 páginas:
- o topo vira `PageHeader` e os emoji viram `Icon`;
- KPIs, tabelas, gráficos e estados passam para os componentes da seção 2;
- os formatadores locais repetidos são trocados pelo `format.ts`;
- `<select>`, `<input>`, botões e abas nativos viram as primitivas shadcn.

Layout, filtros e sequência de uso não mudam.

**Correções que entram no A:**

- **Home (decisão 15):**
  - O texto diz que os dados estão no Snowflake da plataforma Dadosfera, e não mais no PostgreSQL.
  - Entra o card de Fornecedores (5 módulos).
  - O hero fica curto, com números de cobertura vindos dos endpoints existentes. Se algum número não tiver endpoint, fica fora (sem endpoint novo).
  - "Ver módulos" rola com `scrollIntoView`, sem trocar a URL.
- **Datas (decisão 16, só os bugs):**
  - Fornecedores calcula "hoje" pela data local do navegador, e não pela UTC.
  - Leitos usa exatamente 24 meses de calendário, e não 730 dias.
- **Mobile e acessibilidade (decisão 18):**
  - Menu em `Sheet` a 390 px.
  - Campos com altura mínima de 40 px.
  - Foco visível com `--focus-ring` em todos os interativos.
  - Contraste AA em placeholder, botão desabilitado e texto secundário.
  - As duas séries de Leitos com cores distintas, da paleta categórica.
- **Code-split (decisão 20):** as páginas são carregadas com `React.lazy` e `Suspense`, com Skeleton de página.

## 4. Validação e entrega

- **A cada commit:** `npx tsc -b --noEmit` e `npm run build` limpos, e os 105 testes do backend verdes (o backend não muda). A paridade não roda de novo.
- **Smoke Playwright:** os 9 testes, sem e com prefixo (`npm run e2e`, `npm run e2e:prefix`). Os textos dos `<h1>` são mantidos; se um mudar, o teste muda no mesmo commit.
- **Acessibilidade:** `@axe-core/playwright` nas 6 páginas, a 1440 e 390 px. Critério: zero violações `serious` ou `critical`. Arquivo `frontend/e2e/a11y.spec.ts`.
- **Bundle:** `frontend/scripts/check-bundle.mjs` roda depois do build e falha se o chunk JS inicial passar de 250 kB, medido sem gzip.
- **Antes × depois:** o `docs/ux-review/capture.ts` roda de novo a 1440, 1024 e 390 px, e os prints entram numa seção "Antes × depois" do `docs/ux-review/index.html`.
- **QA:** o agente `qa-analyst-frontend`, no modo validação pontual, percorre os fluxos local e publicado em desktop e mobile. Achado de severidade alta volta para correção antes de fechar.
- **Deploy:** `deploy_service.py --start`, `verify.py` 7/7 com `secret_source=env` e smoke contra a URL publicada com SSO.
- **Commits:** um por etapa (tokens, shadcn, shell, componentes, páginas, correções, code-split), com push na `feat/dadosfera-dataapp`.

**Critério de pronto:**
- `grep -rnE "#[0-9a-fA-F]{3,6}\b" frontend/src --include=*.ts --include=*.tsx` não retorna nada, e o CSS só tem hex na camada 1.1.
- Quicksand é a única família carregada.
- Smoke 9/9 nas duas passadas.
- Axe sem violação serious ou critical.
- Chunk inicial abaixo de 250 kB.
- QA sem achado de severidade alta.
- App publicado com o visual novo.

## Riscos

- **Tailwind 4 e shadcn:** o CLI do shadcn para Tailwind 4 gera tokens em `oklch` e um `@theme` próprio. O plano trata a integração como etapa isolada: o gerado é adaptado para apontar para os semânticos, sem manter a paleta padrão do shadcn.
- **`eva-icons`:** o pacote é antigo, com ícones SVG. Se não carregar bem no Vite, os SVGs usados (cerca de 15) são copiados para `src/ui/icons/`, com a licença MIT registrada.
- **Diff grande nas páginas:** a adoção é página a página, com o smoke rodando depois de cada uma, para isolar regressão.
