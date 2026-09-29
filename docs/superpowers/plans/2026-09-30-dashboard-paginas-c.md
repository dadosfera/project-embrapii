# Plano de implementação: Dashboard EMBRAPII, subprojeto C (páginas e visualizações)

**Data:** 30/09/2026 · **Branch:** `feat/dashboard-busca` (sobre `feat/dashboard-beast`) · **Decisões do report de UX:** D6, D10, D11, D12, D13, D14, D16 (períodos), D17
**Specs de referência:** `docs/superpowers/specs/2026-09-25-dashboard-beast-visual-design.md` (A, concluído), `docs/superpowers/specs/2026-09-29-dashboard-busca-catmat-design.md` (B, concluído), `Dashboard/docs/ux-review/index.html` (seções 5 a 8, 10 e 11)

## Objetivo

Compras, Leitos e a aba de leitos do Mapa passam a abrir já carregadas com o filtro padrão. Mudanças de filtro são aplicadas por um botão único, "Aplicar". Compras e Fornecedores abrem em 2020–2025 e filtram por ano. Os gráficos mensais de Compras viram barras anuais com rótulo de valor, e o ano em que um único registro passa de 20% do total ganha barra hachurada e nota. Leitos ganha KPIs em dois níveis, as datas passam para dentro da aba Evolução e o gráfico por UF vira barras empilhadas SUS / não SUS com as 27 UFs rotuladas. Os mapas usam escala por quantis (5 classes), legenda em faixas com unidade e "sem registro" diferente de 0, e passam a funcionar com teclado e toque: tooltip no hover, clique ou Enter fixa a UF, e o painel mostra as 5 maiores quando nada está fixado. Em Fornecedores, clicar numa UF filtra a tabela. A página Mapa continua no menu (D17).

## Arquitetura

- **Backend:** duas rotas novas em `Dashboard/backend/api/compras.py`, cada uma com as versões `Q(pg=..., sf=...)`:
  - `GET /api/compras/intervalo`: MIN/MAX de `data_de_compra`, de onde saem os limites dos seletores de ano de Compras e de Fornecedores, que usam a mesma tabela.
  - `GET /api/compras/por-ano`: série anual mais o maior registro de cada ano, que sustenta o alerta de outlier.

  Nenhuma rota existente muda. Leitos reaproveita `GET /api/leitos/evolucao` (`backend/api/leitos.py:765`), que já existe e tem caso de paridade.
- **Frontend, peças compartilhadas primeiro:**
  - Controles de filtro: `PeriodoAnos`, `BotaoAplicar`, `Alternador`, e o `KpiCard` com a nova prop `destaque`.
  - Escala coroplética: `escalaMapa.ts` e o componente `ChoroplethLegend`.
  - `MapaBrasilUf` interativo.

  Depois, uma tarefa por página. Tudo o que é novo só é importado pelas páginas, que já são lazy (`src/App.tsx:9-14`), então vai para os chunks de rota e não para a entrada (hoje com ~246 KiB, limite de 250 KiB).
- **Não entra neste corte:** leitos por habitante, dado novo, correção do registro de R$ 22,7 bi, reordenação de colunas da tabela de Fornecedores (F3) e rótulos do ranking de fornecedores com nome inteiro (C5).

## Mapa de arquivos

| Arquivo | Tarefa | Tipo |
|---|---|---|
| `Dashboard/backend/api/compras.py` | 1 | alterar (2 rotas) |
| `Dashboard/backend/tests/test_compras_anual.py` | 1 | novo |
| `Dashboard/tests/parity/cases.yaml` | 1 | alterar (casos novos; **não rodar**) |
| `Dashboard/frontend/src/lib/api.ts` | 1, 6 | alterar |
| `Dashboard/frontend/src/lib/ufs.ts` | 2 | novo (lista das 27 UFs, hoje em `pages/Mapa.tsx:80-108`) |
| `Dashboard/frontend/src/ui/periodo.ts` + `periodo.test.ts` | 2 | novo |
| `Dashboard/frontend/src/ui/PeriodoAnos.tsx` | 2 | novo |
| `Dashboard/frontend/src/ui/BotaoAplicar.tsx` | 2 | novo |
| `Dashboard/frontend/src/ui/Alternador.tsx` | 2 | novo |
| `Dashboard/frontend/src/ui/KpiCard.tsx` | 2 | alterar (`destaque`) |
| `Dashboard/frontend/src/ui/filtros.test.tsx` | 2 | novo |
| `Dashboard/frontend/src/ui/escalaMapa.ts` + `escalaMapa.test.ts` | 3 | novo |
| `Dashboard/frontend/src/ui/ChoroplethLegend.tsx` + `ChoroplethLegend.test.tsx` | 3 | novo |
| `Dashboard/frontend/src/index.css` | 3 | alterar (classe `.hachura-sem-registro`) |
| `Dashboard/frontend/src/components/MapaBrasil.tsx` + `MapaBrasil.test.tsx` | 4 | alterar / novo |
| `Dashboard/frontend/src/pages/comprasAnual.ts` + `.test.ts`, `pages/Compras.tsx`, `pages/Compras.test.tsx` | 5 | novo / alterar |
| `Dashboard/frontend/src/pages/leitosUf.ts` + `.test.ts`, `pages/Leitos.tsx`, `pages/Leitos.test.tsx` | 6 | novo / alterar |
| `Dashboard/frontend/src/pages/Mapa.tsx`, `pages/mapaDados.ts` + `.test.ts` | 7 | alterar / novo |
| `Dashboard/frontend/src/pages/Fornecedores.tsx` | 8 | alterar |
| `Dashboard/frontend/e2e/smoke.spec.ts`, `e2e/a11y.spec.ts`, `e2e/prints-c.spec.ts` | 9 | alterar / novo |
| `docs/superpowers/specs/2026-09-25-dashboard-beast-visual-design.md` (tabela de status) | 9 | alterar |

## Já resolvido (A e B), sem trabalho no C

| Achado | Evidência |
|---|---|
| G4/C4, números compactos em KPI e eixo | `pages/Compras.tsx:1277-1300` (`KpiCard` com `moedaCompacta`/`numeroCompacto`), `Compras.tsx:310` e `:1352` (eixos) |
| G5, linha reta com marcador | `ui/chartTheme.ts:52` (`linha.type = "linear"`) e `:55-57` (`dotPara`) |
| C6/M1, dois formulários para CATMAT | `pages/Compras.tsx:1143-1150` e `pages/Mapa.tsx:539-545` usam `CatmatPicker`; no Mapa, escolher já carrega (`Mapa.tsx:349-358`) |
| MP1/M2, estado vazio com causa | `pages/Mapa.tsx:607-612`, `pages/Compras.tsx:1270-1273` |
| F2, data local em Fornecedores | `pages/Fornecedores.tsx:105` com `hojeLocal()` (`ui/format.ts:44-49`) |
| L2, 24 meses de calendário | `pages/Leitos.tsx:95-96` e `:215-221`; `pages/leitosDatas.ts:5-12`, com testes em `leitosDatas.test.ts` |
| L3 (em parte), cores distintas nas séries | `pages/Leitos.tsx:907-908` (`paleta[0]`/`paleta[1]` = primary-500 / info-700). As UFs só ficam todas rotuladas por causa da altura de 24 px (`Leitos.tsx:526`), sem `interval={0}`, e o gráfico continua agrupado em dois; o C resolve |
| F1, cabeçalho padrão em Fornecedores | `pages/Fornecedores.tsx:270-274` |
| G11, code-split por rota | `src/App.tsx:9-14` e `scripts/check-bundle.mjs` |
| G10 (em parte), contraste AA e foco visível | `src/index.css:266` (`:focus-visible`). A parte do mapa (teclado e toque) fica no C |

**Ainda falta, e é o escopo do C:**
- **Compras:** abre com os últimos 12 meses até hoje (`Compras.tsx:351-365`, `umAnoAntesIso`), tem datas por dia (`:1107-1141`), espera o clique em "Pesquisar" (`:1180-1188`, `:1220`) e mostra séries em linha "por mês" (`:1307-1428`).
- **Leitos:** espera o clique em "Aplicar filtros" (`Leitos.tsx:683-691`, `:749`), as datas ficam no bloco geral (`:640-679`), os 6 KPIs têm o mesmo peso (`:801-839`) e o gráfico por UF é agrupado em dois (`:896-932`).
- **Mapa, aba de leitos:** botão "Buscar" e nada carrega ao abrir (`Mapa.tsx:693-702`).
- **Mapa, componente:** escala linear por opacidade (`MapaBrasil.tsx:364-370`), legenda "0 … máx" sem unidade (`:498-512`), UF sem dado pintada como 0 (`:341-345`, `Mapa.tsx:198-208`) e painel que depende só do hover (`:450-451`, `:489-493`).
- **Fornecedores:** período padrão começando em 2015 com datas por dia (`Fornecedores.tsx:107`, `:280-310`), select "UF (tabela)" (`:312-338`) e percentual 0 quando a UF não tem compra (`:61-67`).

## Regras que valem para todas as tarefas

1. **SQL nas duas engines.** Toda query nova é `Q(pg=..., sf=...)`, com os mesmos placeholders e aliases. `backend/tests/test_queries_consistency.py` confere isso sozinho.
2. **Postgres nunca é consultado.** Nenhuma query roda contra o Postgres, que é o banco compartilhado de 39 GB da UFMG; a paridade quem roda é o controlador. As leituras no Snowflake pelo `.env` local estão liberadas.
3. **Guardas do `npm run build`:**
   - `check:tokens`: sem hex em `.ts`/`.tsx`, só `var(--x)` definidas no `index.css`, sem lucide e sem `bg-muted` em `components/ui`;
   - `check:bundle`: a entrada tem de ficar abaixo de 250 KiB. Nada novo pode ser importado de `App.tsx`, `AppShell.tsx` ou `rotas.ts`.
4. **Regras sem camada do `src/index.css`:** `button { font: inherit }` (l. 219), `button:not([data-slot]) { border-radius … !important }` (l. 250) e `:focus-visible { outline }` (l. 266) ganham das utilidades do Tailwind. Então:
   - o tamanho de fonte vai no contêiner;
   - botão próprio leva `data-slot` (ex.: `data-slot="chip"`, como `ChipVariante` em `Medicamentos.tsx:372-376`);
   - para tirar o outline de um elemento SVG, use `style={{ outline: "none" }}` inline.
5. **Cores de Recharts e D3** saem de `categorica()`/`sequencial()` (`ui/chartTheme.ts`) ou de `var(--beast-*)` que exista no `index.css`.
6. **Comandos de verificação:**
   - backend: `cd Dashboard && .venv/bin/python -m pytest backend/tests -q` (base: 127 verdes);
   - frontend: `cd Dashboard/frontend && npx vitest run` (base: 57) e `npm run build`.
7. **Commit por tarefa.** Conventional commit em português, sem push, terminando com:
   ```
   Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
   ```
8. **e2e durante o trabalho.** O smoke de Compras (`e2e/smoke.spec.ts`, teste "Compras: aplica filtros…") e o de Fornecedores (`getByRole("img", { name: /Mapa do Brasil/ })`) quebram nas tarefas 5 e 4/8 e só são corrigidos na tarefa 9. Não rode e2e antes da 9, a não ser para conferir outra coisa.

---

## Tarefa 1. Backend: `/api/compras/intervalo` e `/api/compras/por-ano`

**Depende de:** nada.

**Arquivos:** `Dashboard/backend/api/compras.py`, `Dashboard/backend/tests/test_compras_anual.py` (novo), `Dashboard/tests/parity/cases.yaml`, `Dashboard/frontend/src/lib/api.ts`.

**O que construir**

1. **`GET /api/compras/intervalo`**, sem parâmetros. Resposta:
   ```json
   {"data_minima": "2020-01-01", "data_maxima": "2025-01-01", "ano_minimo": 2020, "ano_maximo": 2025}
   ```
   - PG: `SELECT MIN(c.data_de_compra) AS data_minima, MAX(c.data_de_compra) AS data_maxima FROM mantenedora_compra_produto c;`
   - SF: o mesmo texto, sem `;`.
   - `ano_minimo`/`ano_maximo` são calculados em Python a partir das datas (`.year`, ou `int(str(v)[:4])` se vier string), para as engines não divergirem no `EXTRACT`.
   - Sem linhas, os quatro campos vêm `None`.
   - Erros de banco passam por `_database_error`, igual às outras rotas.
2. **`GET /api/compras/por-ano`**, com os mesmos parâmetros e validação de `/por-mes` (`data_inicio`, `data_fim`, `catmat_id`, `tipo_compra`, via `_params_comuns`, `compras.py:84`). Devolve uma lista ordenada por ano:
   ```json
   [{"ano": 2025, "valor_total": 23200000000.0, "numero_compras": 2474, "quantidade_itens": 1.0,
     "maior_registro": 22702930272.0, "maior_registro_fornecedor": "MEDICAL MERCANTIL ..."}]
   ```
   PG (o `where_sql` é o mesmo fragmento compartilhado):
   ```sql
   WITH base AS (
       SELECT
           EXTRACT(YEAR FROM c.data_de_compra)::int AS ano,
           c.preco_total,
           c.quantidade_de_itens,
           COALESCE(NULLIF(BTRIM(f.nome_fornecedor), ''), 'Nao informado') AS fornecedor,
           ROW_NUMBER() OVER (
               PARTITION BY EXTRACT(YEAR FROM c.data_de_compra)
               ORDER BY c.preco_total DESC NULLS LAST, c.mantenedora_compra_produto_id DESC
           ) AS posicao
       FROM mantenedora_compra_produto c
       LEFT JOIN fornecedor f ON f.fornecedor_id = c.fornecedor_id
       WHERE {where_sql}
   )
   SELECT
       ano,
       COALESCE(SUM(preco_total), 0) AS valor_total,
       COUNT(*) AS numero_compras,
       COALESCE(SUM(quantidade_de_itens), 0) AS quantidade_itens,
       MAX(CASE WHEN posicao = 1 THEN preco_total END) AS maior_registro,
       MAX(CASE WHEN posicao = 1 THEN fornecedor END) AS maior_registro_fornecedor
   FROM base
   GROUP BY ano
   ORDER BY ano;
   ```
   SF: o mesmo, com `YEAR(c.data_de_compra) AS ano`, `PARTITION BY YEAR(c.data_de_compra)`, `TRIM` no lugar de `BTRIM` e sem `;`.
   - O desempate por `mantenedora_compra_produto_id DESC` deixa o fornecedor determinístico nas duas engines.
   - O comentário `# Q(pg, sf): altere as duas versões juntas` vai acima do `Q`, como em `compras.py:112`.
   - `/por-mes` fica como está: tem caso de paridade e o front só deixa de chamá-la.
3. **`cases.yaml`:** entram 4 casos. **Não rode**, porque a paridade é do controlador.
   ```yaml
   - /api/compras/intervalo
   - /api/compras/por-ano?data_inicio={data_inicio}&data_fim={data_fim}
   - /api/compras/por-ano?data_inicio=2020-01-01&data_fim=2025-12-31
   - /api/compras/por-ano?data_inicio=2020-01-01&data_fim=2025-12-31&catmat_id={catmat_compras}&tipo_compra=ADMINISTRATIVA
   ```
4. **`src/lib/api.ts`**, na seção Compras (depois da l. 245):
   ```ts
   export interface IntervaloCompras { data_minima: string | null; data_maxima: string | null; ano_minimo: number | null; ano_maximo: number | null; }
   export interface CompraPorAno { ano: number; valor_total: number; numero_compras: number; quantidade_itens: number; maior_registro: number | null; maior_registro_fornecedor: string | null; }
   export function buscarIntervaloCompras(): Promise<IntervaloCompras>   // request("/api/compras/intervalo")
   export function buscarComprasPorAno(filtros: FiltrosCompras): Promise<CompraPorAno[]>   // request("/api/compras/por-ano", paramsCompras(filtros))
   ```

**Testes (TDD).** Escreva `backend/tests/test_compras_anual.py` antes das rotas. Ele usa `TestClient(app)`, no mesmo padrão de `test_autodrive.py`, e `monkeypatch.setattr(compras, "fetch_all"/"fetch_one", fake)`, onde `compras` é `backend.api.compras`:
- `test_intervalo_deriva_anos_das_datas`: o fake devolve `{"data_minima": date(2020,1,1), "data_maxima": date(2025,1,1)}`, e a resposta tem `ano_minimo == 2020` e `ano_maximo == 2025`;
- `test_intervalo_vazio`: o fake devolve `None`, e os quatro campos vêm `None`;
- `test_por_ano_repassa_filtros`: o fake captura `(query, params)`; os asserts são `params["data_fim_exclusiva"] == date(2026,1,1)`, `"catmat_id"` presente, e `query.for_engine("snowflake")` contendo `YEAR(` e `ROW_NUMBER()`;
- `test_por_ano_data_invertida_400`: `data_fim < data_inicio` devolve 400;
- `test_por_ano_tipo_invalido_400`.

A consistência PG × SF fica com `test_queries_consistency.py`, que pega os `Q` novos sem mudança.

**Verificação**
```bash
cd Dashboard && .venv/bin/python -m pytest backend/tests -q
cd Dashboard && set -a && source .env && set +a && DB_ENGINE=snowflake SNOWFLAKE_DATABASE=DADOSFERA_PRD_DADOSFERADEMO APP_BASE_PATH=/pbp-test_8000 .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8766
curl -s http://127.0.0.1:8766/pbp-test_8000/api/compras/intervalo
curl -s "http://127.0.0.1:8766/pbp-test_8000/api/compras/por-ano?data_inicio=2020-01-01&data_fim=2025-12-31"
```

**Aceite**
- `intervalo` devolve 2020 a 2025.
- `por-ano` devolve 6 linhas (2020 a 2025) com soma de `valor_total` ≈ R$ 50,9 bi.
- 2025 tem `maior_registro` ≈ 22,7 bi e fornecedor contendo "MEDICAL MERCANTIL".
- pytest todo verde, com os casos novos.

**Commit:** `feat(dashboard): rotas de compras por ano e intervalo de datas nas duas engines`

---

## Tarefa 2. Controles compartilhados: período por ano, "Aplicar", alternador e KPI em destaque

**Depende de:** nada. Pode rodar em paralelo com a 1.

**Arquivos:** `src/lib/ufs.ts`, `src/ui/periodo.ts`, `src/ui/periodo.test.ts`, `src/ui/PeriodoAnos.tsx`, `src/ui/BotaoAplicar.tsx`, `src/ui/Alternador.tsx`, `src/ui/KpiCard.tsx`, `src/ui/filtros.test.tsx`. Todos os caminhos são relativos a `Dashboard/frontend/`.

**O que construir**

1. **`src/lib/ufs.ts`:** `export const UFS = ["AC", …, "TO"] as const` (a lista de `pages/Mapa.tsx:80-108`) e `export function ehUf(s: string): boolean`. Não mexa no Mapa ainda; ele troca na tarefa 7.
2. **`src/ui/periodo.ts`**, funções puras:
   - `anosEntre(min: number, max: number): number[]`;
   - `datasDoPeriodo(de: number, ate: number): { data_inicio: string; data_fim: string }` devolve `"AAAA-01-01"` e `"AAAA-12-31"`;
   - `rotuloPeriodo(de, ate)` devolve `"2021"` quando `de === ate` e `"2020–2025"` (meia-risca) nos outros casos;
   - `anoDeIso(iso: string | null): number | null` lê `slice(0,4)` sem passar por `Date`.
3. **`src/ui/PeriodoAnos.tsx`:**
   ```ts
   type Props = { id: string; anos: number[]; de: number; ate: number; onChange: (de: number, ate: number) => void; disabled?: boolean; className?: string };
   ```
   - Um `<fieldset>` com `<legend>` "Período" e dois `Select` shadcn, "De" (`id={`${id}-de`}`) e "Até" (`${id}-ate`), cada um com `<label htmlFor>`, no padrão de `Compras.tsx:1152-1177`.
   - "Até" só oferece anos ≥ `de`. Se o usuário escolhe `de > ate`, `onChange(de, de)`.
   - Um botão "Todos os anos" (`Button` shadcn `variant="outline"` `size="sm"`, que já tem `data-slot`) com `aria-pressed={de === min && ate === max}` e `onChange(min, max)`.
   - Altura mínima de 40 px nos triggers (`h-10 data-[size=default]:h-10`, como no código atual).
4. **`src/ui/BotaoAplicar.tsx`:**
   ```ts
   type Props = { carregando: boolean; pendente?: boolean; type?: "submit" | "button"; onClick?: () => void; ariaLabel?: string; className?: string };
   ```
   - Envolve `Button` shadcn. O rótulo visível é sempre **"Aplicar"**; durante a carga ganha `aria-busy` e `disabled`, sem trocar o nome.
   - Com `pendente`, mostra ao lado `<p role="status" className="text-sm text-muted">Há alterações não aplicadas.</p>`.
   - `ariaLabel` opcional, precisa conter "Aplicar" (regra label-in-name), por exemplo "Aplicar período da evolução".
5. **`src/ui/Alternador.tsx`:** controle segmentado.
   ```ts
   type Props<T extends string> = { rotulo: string; opcoes: { valor: T; rotulo: string }[]; valor: T; onChange: (v: T) => void };
   ```
   - `role="radiogroup"` com `aria-label={rotulo}` e botões `role="radio"`, `data-slot="chip"`, `aria-checked`, no visual de `ChipVariante` (`Medicamentos.tsx:360-389`).
   - Setas esquerda e direita mudam a opção. Tabindex roving: 0 só no marcado.
   - Fonte no contêiner (`text-sm`).
6. **`src/ui/KpiCard.tsx`:** prop nova `destaque?: boolean`. Quando ligada, o `article` ganha `border-primary bg-primary-tint` e o valor passa para `text-3xl sm:text-4xl`. Sem ela, nada muda.

**Testes (TDD).**
- `periodo.test.ts`, primeiro, cobrindo as quatro funções, inclusive `rotuloPeriodo(2021, 2021) === "2021"` e `anoDeIso(null) === null`.
- `filtros.test.tsx`:
  - `PeriodoAnos` renderiza "De" e "Até" com o ano atual e "Todos os anos" chama `onChange(2020, 2025)`;
  - `BotaoAplicar` tem nome "Aplicar" com e sem carga e mostra o aviso quando `pendente`;
  - `Alternador`: a seta direita move o `aria-checked`;
  - `KpiCard destaque` mantém o valor compacto.
- Radix Select em jsdom pede o stub de `ResizeObserver` e `hasPointerCapture`; siga o padrão de `components.test.tsx:34-40`.

**Verificação:** `cd Dashboard/frontend && npx vitest run && npm run build`.

**Aceite:** testes novos verdes, build limpo e bundle de entrada inalterado, porque nada disso é importado pelo shell.

**Commit:** `feat(dashboard): controles de periodo por ano, botao Aplicar, alternador e KPI em destaque`

---

## Tarefa 3. Escala coroplética por quantis e `ChoroplethLegend`

**Depende de:** nada.

**Arquivos:** `src/ui/escalaMapa.ts`, `src/ui/escalaMapa.test.ts`, `src/ui/ChoroplethLegend.tsx`, `src/ui/ChoroplethLegend.test.tsx`, `src/index.css`.

**O que construir**

1. **`src/ui/escalaMapa.ts`**, puro e sem d3-scale, para caber num teste simples:
   ```ts
   export type ClasseMapa =
     | { tipo: "sem-registro" }
     | { tipo: "zero" }
     | { tipo: "faixa"; indice: number; min: number; max: number };
   export type EscalaMapa = { classeDe(v: number | null | undefined): ClasseMapa; faixas: { indice: number; min: number; max: number }[] };
   export function escalaQuantis(valores: (number | null | undefined)[], k = 5): EscalaMapa;
   export function rotuloFaixa(f: { min: number; max: number }, formatar: (v: number) => string): string; // "1–500", ou "500" se min === max
   ```
   - `null`/`undefined` vira `sem-registro`, `0` vira `zero`, e os quantis são calculados só sobre os valores maiores que 0.
   - Os valores positivos são ordenados. O limiar de cada classe `i` (de 1 a k−1) é `ordenados[Math.floor(i * n / k)]`. Limiares repetidos são removidos, então valores iguais nunca ficam em classes diferentes, e com menos de 5 valores distintos o número de classes cai junto.
   - O índice da classe é a quantidade de limiares ≤ v. `faixas[i]` guarda o min e o max reais dos membros.
2. **`src/index.css`:** classe fora da camada de tokens e sem hex:
   ```css
   .hachura-sem-registro { background: repeating-linear-gradient(45deg, var(--beast-basic-200) 0 3px, var(--beast-basic-600) 3px 4px); }
   ```
3. **`src/ui/ChoroplethLegend.tsx`:**
   ```ts
   type Props = { escala: EscalaMapa; cores: string[]; unidade: string; formatar: (v: number) => string; mostrarSemRegistro?: boolean; mostrarZero?: boolean };
   ```
   - `<figure>` com `<figcaption>` "Legenda ({unidade})" e uma `<ul>` na ordem "sem registro" (amostra `.hachura-sem-registro` com borda `border-line`), "0" (amostra `bg-subtle` com borda) e as faixas em ordem crescente com a cor `cores[i]`.
   - As amostras são `span aria-hidden` de 14 × 14 px.
   - `mostrarSemRegistro` e `mostrarZero` vêm de fora; por padrão, só aparece o que existir nos dados.
   - O texto usa `tabular-nums text-xs text-muted`.

**Testes (TDD).** `escalaMapa.test.ts` primeiro:
- 27 valores positivos distintos dão 5 faixas e todo valor cai numa delas;
- `[0, null, 10, 10, 10]` dá `zero`, `sem-registro` e uma faixa só;
- valores empatados na borda ficam na mesma classe;
- dois valores positivos distintos dão 2 faixas;
- `rotuloFaixa({min: 1, max: 500}, numeroExato) === "1–500"`.

`ChoroplethLegend.test.tsx`: aparecem "sem registro", "0" e as 5 faixas com a unidade na legenda.

**Verificação:** `cd Dashboard/frontend && npx vitest run && npm run build` (o `check:tokens` tem de aceitar a classe nova).

**Aceite:** testes verdes e nenhum hex fora da camada `beast:tokens`.

**Commit:** `feat(dashboard): escala por quantis e legenda em faixas com sem registro para os mapas`

---

## Tarefa 4. `MapaBrasilUf` interativo e acessível

**Depende de:** tarefa 3.

**Arquivos:** `src/components/MapaBrasil.tsx`, `src/components/MapaBrasil.test.tsx` (novo).

**O que construir.** A API muda de forma compatível: Mapa e Fornecedores continuam compilando sem alteração.

```ts
export type DadoMapaUf = { uf: string; valor: number | null };  // null ou UF ausente = sem registro
type MapaBrasilUfProps = {
  dados: DadoMapaUf[]; titulo?: string; descricao?: string; tituloValor?: string; fonte?: string;
  unidade?: string;                       // "unidades", "leitos", "%"; padrão "valor"
  formatar?: (v: number) => string;       // padrão numeroExato
  ufFixada?: string | null;               // controlado (Fornecedores); se undefined, estado interno
  onFixarUf?: (uf: string | null) => void;
};
```

1. **Cor.** Saem `maiorValor` (`MapaBrasil.tsx:292-302`) e a opacidade linear (`:364-370`). A cor passa a vir de `escalaQuantis(valores)` e `sequencial()`, que tem 5 cores (`chartTheme.ts:7-10`):
   - `faixa` usa `cores[indice]`;
   - `zero` usa `var(--beast-basic-300)`;
   - `sem-registro` usa `url(#${idBase}-sem-registro)`, um `<pattern>` em `<defs>` dentro do SVG com `rect` em `var(--beast-basic-200)` e linhas diagonais em `var(--beast-basic-600)`.
   - `idBase` é `useId().replace(/[^a-zA-Z0-9_-]/g, "")`, porque o `useId` do React 19 gera caracteres que quebram `url(#…)`.
   - UF que não aparece em `dados` é `sem registro` e deixa de ser 0 (hoje é `?? 0`, em `:341-345`).
2. **Semântica.**
   - O `<svg>` passa de `role="img"` para `role="group"`, com `aria-label={`Mapa do Brasil: ${titulo}`}`.
   - Cada `<path>` recebe `tabIndex={0}`, `role="button"`, `aria-pressed={fixada === sigla}` e `aria-label="Minas Gerais (MG): 1.234 unidades"` (ou "…: sem registro"). O `<title>` sai, porque duplicaria o nome.
   - Estilo inline `style={{ outline: "none" }}`, já que o `:focus-visible` global não desenha direito em SVG. O foco fica visível num contorno sobreposto (item 4).
3. **Interação.**
   - `onMouseEnter`/`onFocus` definem a UF em hover; `onMouseLeave`/`onBlur` limpam.
   - `onClick` e `onKeyDown` com Enter ou Espaço alternam a fixação: `onFixarUf?.(nova)` ou o estado interno.
   - Escape limpa a fixação.
   - Toque usa o mesmo `onClick`.
4. **Contorno sobreposto.** Depois de todos os paths, um `<path d=… fill="none" stroke="var(--focus-ring)" strokeWidth={3} pointerEvents="none" aria-hidden>` para a UF fixada e outro, com `var(--text)`, para a UF em hover ou foco. Não reordene os paths, porque mover no DOM o elemento focado faz ele perder o foco.
5. **Tooltip no hover.** Um `div` absoluto dentro do contêiner `relative`, com `aria-hidden` (o leitor de tela recebe o painel) e posição por `event.clientX - rect.left`. Mostra nome, sigla e valor formatado com a unidade. Some no `mouseleave`.
6. **Painel lateral**, o `aside` atual de `:464-494`, com `aria-live="polite"`:
   - com UF fixada, ou em hover/foco: nome, sigla, valor grande (`formatar` + unidade, ou "sem registro") e, se estiver fixada, `Button` shadcn `variant="ghost"` "Limpar seleção";
   - sem nada: título "5 maiores" e uma `<ol>` com as 5 UFs de maior valor, cada uma um `Button variant="ghost"` que fixa a UF.
   - O texto "Passe o mouse…" sai.
7. **Legenda.** O gradiente `0 … máx` (`:498-512`) sai e entra `<ChoroplethLegend escala cores unidade formatar />`.

**Testes (TDD).** `MapaBrasil.test.tsx`, primeiro:
- `vi.stubGlobal("fetch", …)` devolve um `FeatureCollection` com 3 quadrados (MG, SP, AC), com a `sigla` nas `properties`;
- `render(<MapaBrasilUf dados={[{uf:"MG",valor:10},{uf:"SP",valor:0}]} unidade="unidades" />)`;
- os asserts:
  - `findByRole("button", { name: /MG.*10 unidades/ })` existe;
  - AC tem nome contendo "sem registro";
  - `fill` de AC começa com `url(#`;
  - o fill de SP é diferente do de MG;
  - `fireEvent.keyDown(mg, { key: "Enter" })` deixa `aria-pressed="true"` e o painel mostra "Minas Gerais" (ou a sigla, se o fixture não tiver nome);
  - Escape limpa;
  - sem seleção, o painel lista "5 maiores";
  - no modo controlado, clicar chama `onFixarUf("MG")`.

Zere o cache de módulo (`geojsonCache`) entre testes com `vi.resetModules()` e import dinâmico.

**Verificação:** `cd Dashboard/frontend && npx vitest run && npm run build`.

**Aceite:** testes verdes; nenhum hex; Mapa e Fornecedores compilam sem alteração. O smoke de Fornecedores, que procura o `img`, quebra aqui e é corrigido na tarefa 9.

**Commit:** `feat(dashboard): mapa por quantis, sem registro hachurado e UF fixavel por teclado e toque`

---

## Tarefa 5. Compras: abre em 2020–2025, filtro por ano, "Aplicar", barras anuais e alerta de outlier

**Depende de:** tarefas 1 e 2.

**Arquivos:** `src/pages/comprasAnual.ts` + `comprasAnual.test.ts` (novos), `src/pages/Compras.tsx`, `src/pages/Compras.test.tsx` (novo).

**O que construir**

1. **`src/pages/comprasAnual.ts`**, puro:
   ```ts
   export const LIMITE_OUTLIER = 0.2;
   export type AnoCompras = { ano: number; valor_total: number; numero_compras: number; maior_registro: number | null; maior_registro_fornecedor: string | null; participacao_maior: number | null; outlier: boolean };
   export function anotarOutliers(linhas: CompraPorAno[], limite = LIMITE_OUTLIER): AnoCompras[];
   export function notaOutlier(a: AnoCompras): string; // "2025: 1 registro (MEDICAL MERCANTIL …) = R$ 22,7 bi, 97,9% do valor do ano."
   ```
   - A regra: `outlier = numero_compras > 1 && valor_total > 0 && maior_registro / valor_total > limite`. O limite é estrito. Um ano com um único registro não é marcado, porque seria sempre 100% e a nota não diria nada.
   - A coerção numérica segue `numero()` (`Compras.tsx:101-112`).
2. **`Compras.tsx`, estado e carga.**
   - Saem `hojeIso`/`umAnoAntesIso` (`:164-219`) e `dataInicio`/`dataFim` (`:351-365`). Entram `anos: number[]`, `anoDe` e `anoAte`, vindos de `buscarIntervaloCompras()` num `useEffect` de montagem. Se o intervalo falhar, aparece `ErrorState` com uma nova tentativa.
   - `aplicarFiltros(event)` (`:421-560`) é dividida em `carregar(f: { anoDe; anoAte; grupo; tipo })`, que monta `FiltrosCompras` com `datasDoPeriodo()`, e no `onSubmit` do form. Quando o intervalo chega, `carregar` roda sozinha com os limites (2020–2025), o grupo `null` e o tipo "Todos".
   - Um contador `pedido = useRef(0)` descarta respostas antigas, no padrão de `Mapa.tsx:323` e `:363-371`.
   - `Promise.all` troca `buscarComprasPorMes` por `buscarComprasPorAno`, e `DadosCompras.porMes` vira `porAno: CompraPorAno[]`.
   - `pendente` compara o form com `filtrosConfirmados`, que passa a guardar `anoDe`, `anoAte`, `catmat_id` e `tipo`.
3. **Formulário** (`:1101-1189`):
   - as duas `Input type="date"` dão lugar a `<PeriodoAnos id="compras-periodo" … className="sm:col-span-2">`;
   - `CatmatPicker` e o tipo continuam;
   - os rótulos do tipo passam a "Administrativa" e "Judicial", com os valores `ADMINISTRATIVA`/`JUDICIAL` inalterados;
   - o botão vira `<BotaoAplicar type="submit" carregando={carregando} pendente={pendente} />`;
   - a instrução de `:1214-1223` ("clique em Pesquisar") sai, porque a página já abre carregada.
4. **Resumo aplicado** (`:1246-1263`): "Período: **2020–2025**", com `rotuloPeriodo`, no lugar das duas datas.
5. **Seção "Evolução anual das compras"** (`:1307-1428`), dois `ChartFrame` com `BarChart` vertical e `XAxis dataKey="ano"`:
   - **"Valor total comprado por ano":**
     - uma `<Cell>` por linha, com `fill={a.outlier ? `url(#${idHachura})` : paleta[0]}`;
     - `<defs><pattern id={idHachura} patternUnits="userSpaceOnUse" width={6} height={6} patternTransform="rotate(45)"><rect width={6} height={6} fill="var(--beast-primary-100)" /><line x1={0} y1={0} x2={0} y2={6} stroke={paleta[0]} strokeWidth={3} /></pattern></defs>` dentro do `BarChart`, com `idHachura` saneado como na tarefa 4;
     - `<LabelList dataKey="valor_total" position="top" formatter={(v) => moedaCompacta(v)} />`, com um `*` no rótulo do ano marcado (`content` próprio ou `formatter` por índice);
     - tooltip com `moedaExata`;
     - abaixo do gráfico, se algum ano estiver marcado: uma legenda com amostra hachurada e o texto "Barra hachurada: um único registro passa de 20% do valor do ano. O registro foi mantido.", seguida de uma `<ul>` com `notaOutlier(a)` para cada ano marcado.
   - **"Registros de compra por ano":** barras em `paleta[0]` com `LabelList` em `numeroCompacto`, sem hachura.
   - O `EmptyState` "Sem série mensal" vira "Sem série anual".
6. **KPI "Valor total comprado"** (`:1277-1282`): se houver ano marcado, `hint="Inclui 1 registro de R$ 22,7 bi em 2025; veja a nota no gráfico anual."`, montado a partir do maior outlier.
7. Saem `rotuloMes`, `MESES_CURTOS`, `LineChart`/`Line`/`dotPara` e o import de `Input`, se ficarem sem uso.

**Testes (TDD)**
- **`comprasAnual.test.ts`, primeiro:**
  - 2025 com `valor_total` 23,2e9, 2.474 compras e `maior_registro` 22,7e9 é marcado, e `notaOutlier` casa com `/2025: 1 registro \(MEDICAL MERCANTIL\) = R\$\s22,7\sbi, 97,\d% do valor do ano\./`;
  - exatamente 20% não é marcado;
  - `valor_total` 0 não é marcado;
  - `numero_compras` 1 não é marcado.
- **`Compras.test.tsx`:**
  - `vi.mock("../lib/api")`, com `buscarIntervaloCompras` devolvendo 2020–2025 e as demais funções devolvendo fixtures, mais o stub de `ResizeObserver`;
  - render dentro de `MemoryRouter` e `TooltipProvider`;
  - sem nenhum clique, `buscarKpisCompras` é chamada com `data_inicio: "2020-01-01"` e `data_fim: "2025-12-31"`;
  - existe `getByRole("button", { name: "Aplicar" })`;
  - com a fixture de outlier, aparece o texto "1 registro".

**Verificação:** `cd Dashboard/frontend && npx vitest run && npm run build`. Depois, conferência manual contra o uvicorn da tarefa 1, sempre refazendo o build e reiniciando o uvicorn, porque `backend/static.py` guarda o `index.html` em cache.

**Aceite**
- `/compras` abre carregada em 2020–2025, sem clique, com KPI "R$ 50,9 bi" e 6 barras rotuladas.
- 2025 aparece hachurada, com a nota.
- Trocar "De" para 2021 mostra "Há alterações não aplicadas" e "Aplicar" recarrega.
- Não sobra nenhum `type="date"` na página.

**Commit:** `feat(dashboard): Compras abre em 2020-2025 com filtro por ano, barras anuais e alerta de outlier`

---

## Tarefa 6. Leitos: carga ao abrir, KPIs em dois níveis, datas na aba Evolução e barras empilhadas por UF

**Depende de:** tarefa 2.

**Arquivos:** `src/lib/api.ts`, `src/pages/leitosUf.ts` + `leitosUf.test.ts` (novos), `src/pages/Leitos.tsx`, `src/pages/Leitos.test.tsx` (novo).

**O que construir**

1. **`api.ts`:** `export function buscarEvolucaoLeitos(uf: string, dataInicio: string, dataFim: string): Promise<EvolucaoLeitos[]>`, chamando `request("/api/leitos/evolucao", { data_inicio, data_fim, uf })`. A rota já existe (`leitos.py:765`), está na paridade e não depende de `modo`.
2. **`src/pages/leitosUf.ts`**, puro:
   ```ts
   export type MetricaUf = "gerais" | "uti";
   export type BarraUf = { uf: string; sus: number; nao_sus: number; total: number; percentual_sus: number | null };
   export function barrasEmpilhadasUf(porUf: LeitosPorUf[], metrica: MetricaUf): BarraUf[];
   ```
   - "gerais" usa `leitos_gerais`/`leitos_sus`; "uti" usa `leitos_uti`/`leitos_uti_sus`.
   - `nao_sus = max(0, total − sus)`.
   - Fica só o que `ehUf(uf)` aceita (`src/lib/ufs.ts`), para "Nao informado" não virar a 28ª barra.
   - Ordem: total decrescente, e `uf` em ordem crescente no empate.
3. **Carga ao abrir.**
   - O `useEffect` de opções (`Leitos.tsx:198-237`) define as datas e, no mesmo fluxo, chama `carregarPainel({ modo: "ultima_competencia", uf: "" }, inicio, fim)`.
   - `aplicarFiltros` (`:240-291`) vira `carregarPainel(filtros, inicio, fim)` mais o `onSubmit`.
   - O aviso "clique em Aplicar filtros" (`:741-752`) sai.
   - O `useRef` de pedido descarta respostas fora de ordem.
4. **Filtros gerais** (`:541-693`):
   - ficam só "Base utilizada nos indicadores" e "Unidade Federativa";
   - o parágrafo "O período é aplicado somente à evolução histórica." (`:548-550`) sai;
   - o botão vira `<BotaoAplicar type="submit" carregando={carregando} pendente={modo/uf ≠ confirmados} />`;
   - o submit usa as datas de evolução já confirmadas.
5. **Aba "Evolução histórica"** (`:976-1020`). No topo da aba entra um form pequeno:
   - as duas `Input type="date"` que hoje estão em `:640-679`, com os mesmos ids `inicio-evolucao` e `fim-evolucao` e o mesmo `min`/`max`;
   - `<BotaoAplicar type="submit" ariaLabel="Aplicar período da evolução" carregando={carregandoEvolucao} pendente={…} />`;
   - no submit: validação (início ≤ fim), `buscarEvolucaoLeitos(filtrosConfirmados.uf, inicio, fim)`, que troca só `dados.evolucao` e as datas confirmadas, sem recarregar o painel inteiro;
   - erro de validação aparece em linha dentro da aba;
   - o resumo "Filtros aplicados" (`:773-790`) perde o trecho "Evolução: …", que continua no `subtitle` do gráfico (`:992`).
6. **KPIs em dois níveis** (`:801-839`):
   - primeira linha, `grid sm:grid-cols-2`: `KpiCard destaque` "Leitos gerais" e `KpiCard destaque` "Participação do SUS", este com `hint={`${numeroCompacto(leitos_sus)} leitos SUS. Percentual dos leitos gerais destinados ao SUS.`}`;
   - segunda linha, `grid sm:grid-cols-3`: "Leitos de UTI", "Leitos de UTI SUS" e "Instituições com registro";
   - o card "Leitos SUS" isolado sai, porque o número foi para o hint;
   - o skeleton (`:757-761`) acompanha: 2 blocos maiores e 3 menores.
7. **Aba "Distribuição por UF"** (`:882-937`):
   - o grid de dois gráficos dá lugar a um `ChartFrame` só, "Leitos por UF, SUS e não SUS";
   - `legend={<Alternador rotulo="Tipo de leito" opcoes={[{valor:"gerais",rotulo:"Gerais"},{valor:"uti",rotulo:"UTI"}]} … />}`;
   - `BarChart layout="vertical" data={barras} barCategoryGap={3}`;
   - `YAxis type="category" dataKey="uf" interval={0} width={36}`;
   - `<Bar dataKey="sus" stackId="uf" name="SUS" fill={paleta[0]} />` e `<Bar dataKey="nao_sus" stackId="uf" name="Não SUS" fill={paleta[1]} radius={[0,4,4,0]} />`;
   - a altura é `barras.length * 22 + 56`, e a constante antiga `alturaUf` (`:526`) sai;
   - o tooltip mostra os valores exatos e o "% SUS";
   - a tabela continua, com `pageSize={27}` para não paginar.

**Testes (TDD)**
- **`leitosUf.test.ts`, primeiro:** ordenação por total; `nao_sus` nunca negativo; "Nao informado" filtrado; a métrica "uti" usa as colunas de UTI.
- **`Leitos.test.tsx`:**
  - `vi.mock("../lib/api")`, com `buscarOpcoesLeitos` devolvendo `data_maxima: "2026-01-01"`;
  - sem clique, `buscarPainelLeitos` é chamada com `("2024-01-01", "2026-01-01")`, a data de `inicioHaMeses`;
  - "Leitos gerais" e "Participação do SUS" aparecem na primeira linha;
  - abrir a aba Evolução, mudar o início e clicar em "Aplicar período da evolução" chama `buscarEvolucaoLeitos` e **não** chama `buscarPainelLeitos` de novo;
  - o `Alternador` "UTI" troca as barras (confira pelo nome da série ou pelos dados).

**Verificação:** `cd Dashboard/frontend && npx vitest run && npm run build`, mais conferência manual a 1440 px e 390 px.

**Aceite**
- `/leitos` abre carregada, com a competência mais recente e todas as UFs.
- 2 KPIs em destaque e 3 secundários.
- As datas só aparecem na aba Evolução.
- Um gráfico empilhado com 27 rótulos de UF, ordenado por total, e o alternador Gerais | UTI.
- Não sobra o texto "Aplicar filtros".

**Commit:** `feat(dashboard): Leitos carrega ao abrir, KPIs em dois niveis, periodo na aba Evolucao e barras empilhadas por UF`

---

## Tarefa 7. Mapa: "sem registro", leitos carregando ao abrir, "Aplicar" e % SUS

**Depende de:** tarefas 2, 3 e 4.

**Arquivos:** `src/pages/Mapa.tsx`, `src/pages/mapaDados.ts` + `mapaDados.test.ts` (novos).

**O que construir**

1. **`src/pages/mapaDados.ts`:** `normalizarEstoque` e `normalizarLeitos` saem de `Mapa.tsx:161-283` e passam a devolver `null` para a UF ausente, no lugar de 0. Usam `UFS` de `src/lib/ufs.ts`, e a lista local (`Mapa.tsx:80-108`) é removida.
   ```ts
   export type LinhaEstoque = { uf: string; estoque_total: number | null; num_instituicoes: number | null };
   export type LinhaLeitos = { uf: string; leitos_gerais: number | null; …; percentual_sus: number | null };
   export function ordenarNulosPorUltimo<T>(linhas: T[], chave: (l: T) => number | null): T[];
   ```
   `percentual_sus` é `leitos_sus / leitos_gerais * 100` quando `gerais > 0`; nos outros casos, `null`.
2. **Aba Estoque:**
   - `dadosMapaEstoque` repassa `valor: null`;
   - `<MapaBrasilUf … unidade="unidades" formatar={quantidade} />`;
   - as células da tabela mostram "sem registro" quando o valor é `null`, pelo `quantidade(null)`/`numeroExato(null)`, que já devolvem `SEM_DADO`. Se a página preferir "sem registro", o formatador local vira `v == null ? "sem registro" : …`;
   - o texto de `:595` ("UFs sem registro são mantidas com valor zero.") passa a dizer: "UFs sem registro aparecem hachuradas no mapa e como 'sem registro' na tabela; 0 indica registro com estoque zerado."
3. **Aba Leitos:**
   - carrega ao abrir: um `useEffect` com `aba === "leitos" && !leitosBruto && !carregandoLeitos && falhaLeitos == null` chama `buscarMapaLeitos()` com o modo padrão;
   - o botão "Buscar" (`:693-702`) vira `<BotaoAplicar type="button" onClick={buscarMapaLeitos} carregando={carregandoLeitos} pendente={modoLeitos !== modoLeitosAplicado} />`;
   - o texto de `:625-627` passa a "A base é aplicada com o botão Aplicar; a métrica muda o mapa na hora.";
   - a métrica `percentual_sus` entra em `MetricaLeitos` (`:56-60`), `ROTULOS_METRICA` e no Select (`:683-686`) como "Participação do SUS (%)". É a **métrica padrão**, conforme a proposta da seção 7 do report;
   - `unidade` é "%" (formatador de percentual com uma casa, como `Fornecedores.tsx:52-58`) para `percentual_sus` e "leitos" (`numeroExato`) para as demais;
   - a coluna "Leitos SUS (%)" entra na tabela.

**Testes (TDD).** `mapaDados.test.ts`, primeiro:
- UF ausente vira `null`, e 0 continua 0;
- `percentual_sus` fica `null` com `gerais` 0;
- a lista tem as 27 UFs;
- `ordenarNulosPorUltimo` põe os nulos no fim.

**Verificação:** `cd Dashboard/frontend && npx vitest run && npm run build`, mais conferência manual com a dipirona 500 (CATMAT `BR0267203`) e a aba Leitos.

**Aceite**
- A aba Leitos mostra o mapa sem clique, com "% SUS" como padrão.
- A legenda aparece em faixas com unidade, e o "sem registro" hachurado aparece quando alguma UF não tem dado.
- Tab e Enter fixam a UF, e o painel mostra as 5 maiores quando nada está fixado.
- Não sobra botão "Buscar" na página.

**Commit:** `feat(dashboard): Mapa com sem registro distinto de zero, leitos carregando ao abrir e % SUS`

---

## Tarefa 8. Fornecedores: período por ano (2020–2025) e clique na UF filtrando a tabela

**Depende de:** tarefas 1 (só o `buscarIntervaloCompras` no `api.ts`), 2 e 4.

**Arquivos:** `src/pages/Fornecedores.tsx`.

**O que construir**

1. **Período.**
   - `dataInicio`/`dataFim` (`Fornecedores.tsx:105-108`) dão lugar a `anos`, `anoDe` e `anoAte`, vindos de `buscarIntervaloCompras()`. A tabela é a mesma de Compras, `mantenedora_compra_produto`, e o padrão é o intervalo inteiro (2020–2025).
   - Enquanto o intervalo carrega, a barra de filtros mostra um `Skeleton` e os efeitos de mapa e ranking não disparam (guarda `if (anoDe == null) return`).
   - Os efeitos (`:122-171`) usam `datasDoPeriodo(anoDe, anoAte)`.
   - **Fornecedores continua aplicando na hora**, sem botão "Aplicar". Ela sempre carregou sozinha, e o seletor é discreto. O controle é o mesmo `PeriodoAnos` de Compras (`id="fornecedores-periodo"`).
   - `hojeLocal` sai do import se ficar sem uso.
2. **UF pelo mapa.**
   - O Select "UF (tabela)" (`:312-338`) e `TODAS_UFS` (`:48`) saem.
   - `<MapaBrasilUf … ufFixada={ufFiltro || null} onFixarUf={(uf) => setUfFiltro(uf ?? "")} unidade="%" formatar={percentual} tituloValor="% de itens estrangeiros" />`.
   - Acima da tabela entra uma linha de estado: "Tabela: todas as UFs. Clique numa UF do mapa para filtrar." ou "Tabela filtrada por **MG**" com `Button variant="outline" size="sm"` "Limpar UF".
   - O texto de `descricao` do mapa (`:381`) ganha: "Clique numa UF para filtrar o ranking."
3. **Sem registro.** `calcularPercentualEstrangeiro` (`:61-67`) passa a devolver `number | null`, com `null` quando o total for 0. UFs sem compra no período já não vêm da API e ficam "sem registro".

**Testes.** Em `src/pages/Fornecedores.test.tsx` (novo):
- `vi.mock("../lib/fornecedoresApi")` e `vi.mock("../lib/api")` (intervalo 2020–2025), com `fetch` do GeoJSON stubado como na tarefa 4;
- na montagem, `buscarRankingFornecedores` é chamada com `("2020-01-01", "2025-12-31", undefined, 100)`;
- clicar no botão da UF "MG" do mapa chama de novo com `"MG"` e mostra "Tabela filtrada por MG";
- "Limpar UF" volta para `undefined`;
- não existe `getByLabelText("UF (tabela)")`.

**Verificação:** `cd Dashboard/frontend && npx vitest run && npm run build`.

**Aceite**
- `/fornecedores` abre em 2020–2025, sem datas por dia.
- Clicar numa UF, ou Enter com ela focada, filtra o ranking.
- A legenda aparece em faixas de %, com unidade.
- Não sobra o select "UF (tabela)".

**Commit:** `feat(dashboard): Fornecedores com periodo por ano e filtro de UF pelo mapa`

---

## Tarefa 9. e2e, acessibilidade, prints 1440/1024/390 e status dos specs

**Depende de:** tarefas 1 a 8.

**Arquivos:** `Dashboard/frontend/e2e/smoke.spec.ts`, `Dashboard/frontend/e2e/a11y.spec.ts`, `Dashboard/frontend/e2e/prints-c.spec.ts` (novo, tag `@slow`), `docs/superpowers/specs/2026-09-25-dashboard-beast-visual-design.md` e `docs/superpowers/specs/2026-09-29-dashboard-busca-catmat-design.md` (status).

**O que fazer**

1. **`smoke.spec.ts`:**
   - **Fornecedores** (bloco `if (rota === "fornecedores")`): passa a procurar `getByRole("group", { name: /Mapa do Brasil/ })`.
   - **Compras:** o teste "aplica filtros com dados conhecidos" é trocado por dois:
     - **"Compras abre carregada em 2020–2025"**: `page.waitForResponse` numa URL de `/api/compras/kpis` com `data_inicio=2020-01-01` e `data_fim=2025-12-31`, disparada **sem clique**; o KPI "Valor total comprado" contém "R$"; aparece o texto "1 registro" (nota do outlier de 2025);
     - **"Compras aplica ano e medicamento"**: escolhe "De" = 2021 (Radix: clicar em `#compras-periodo-de` e depois na `option` "2021"), faz `escolherCatmat(page, "#produto-compras", "lamotrigina 100", …)` e clica em `getByRole("button", { name: "Aplicar", exact: true })`; a requisição de KPIs precisa ter `data_inicio=2021-01-01`.
   - **Leitos, novo:** abre com o KPI "Leitos gerais" preenchido e sem clique; a aba "Distribuição por UF" tem 27 ticks no eixo Y (`.recharts-yAxis .recharts-cartesian-axis-tick`); a aba "Evolução histórica" mostra `#inicio-evolucao`.
   - **Mapa, novo:** a aba "Leitos por estado" carrega sem clique; `getByRole("button", { name: /\(MG\):/ })` recebe foco e Enter, e o painel mostra "Minas Gerais"; a legenda contém a unidade.
   - **Fornecedores, novo:** clicar na UF SP dispara `/api/fornecedores/ranking` com `uf=SP` e aparece "Tabela filtrada por SP".
2. **`a11y.spec.ts`:** as `INTERACOES` (`a11y.spec.ts:30-68`) estão velhas desde o B (ainda usam "Buscar", select e "Pesquisar") e são reescritas:
   - medicamentos e mapa com o helper `escolherCatmat` (copiado do smoke);
   - compras só espera o KPI;
   - entram `leitos` (espera o KPI) e `fornecedores` (fixa uma UF por teclado).
   - O critério continua: zero violações `serious`/`critical` a 1440 px e 390 px.
3. **`prints-c.spec.ts`**, com `@slow`: um teste por largura (1440, 1024 e 390) que faz `page.screenshot({ fullPage: true, path: test-results/prints-c/<pagina>-<largura>.png })`. `test-results/` já está no `.gitignore` do front, então os prints não são versionados, como no B. Estados:
   - compras padrão;
   - leitos padrão e aba Evolução;
   - mapa estoque (dipirona 500) com MG fixada, e mapa leitos;
   - fornecedores com SP fixada.
4. **Conferência visual dos prints:**
   - hachura em 2025;
   - 27 UFs legíveis a 390 px;
   - painel do mapa embaixo do mapa a 390 px;
   - legenda sem quebra feia a 1024 px.

   Se algo não passar, corrija na página e registre no commit desta tarefa.
5. **Specs:** na tabela de status do spec A (`2026-09-25-…-design.md`), a linha C passa a "Implementado em 30/09 (branch `feat/dashboard-busca`); paridade dos casos novos pendente (controlador)". No spec B, a observação "O filtro de Compras continua com o botão 'Pesquisar'" é marcada como resolvida.

**Verificação**
```bash
cd Dashboard/frontend && npm run build && npx vitest run
cd Dashboard && .venv/bin/python -m pytest backend/tests -q
# (re)iniciar o backend DEPOIS do build (static.py guarda o index.html em cache):
cd Dashboard && set -a && source .env && set +a && DB_ENGINE=snowflake SNOWFLAKE_DATABASE=DADOSFERA_PRD_DADOSFERADEMO APP_BASE_PATH=/pbp-test_8000 .venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8766
cd Dashboard/frontend && E2E_BASE_URL=http://127.0.0.1:8766/pbp-test_8000/ npx playwright test e2e/smoke.spec.ts
cd Dashboard/frontend && E2E_BASE_URL=http://127.0.0.1:8766/pbp-test_8000/ npx playwright test e2e/a11y.spec.ts
cd Dashboard/frontend && E2E_BASE_URL=http://127.0.0.1:8766/pbp-test_8000/ npx playwright test e2e/prints-c.spec.ts --grep @slow
```

**Aceite**
- Smoke todo verde, com os novos testes de Compras, Leitos, Mapa e Fornecedores.
- Axe sem `serious`/`critical` nas 6 rotas, com e sem dados, a 1440 px e 390 px.
- Entrada abaixo de 250 KiB no `check:bundle`.
- Prints conferidos nas três larguras.
- Specs atualizados.

**Commit:** `test(dashboard): smoke e axe dos fluxos do subprojeto C e prints 1440/1024/390`

---

## Riscos e notas

- **Paridade.** As duas rotas novas foram escritas para as duas engines, mas só rodaram no Snowflake. O `cases.yaml` ganha os 4 casos e o controlador roda a paridade contra o Postgres. Pontos de atenção:
  - `EXTRACT(YEAR …)::int` × `YEAR()`;
  - `ROW_NUMBER` com o mesmo desempate nas duas;
  - `BTRIM` × `TRIM`.
- **Outlier com filtro de produto.** Com um CATMAT filtrado, os anos têm poucos registros e o limite de 20% marca com frequência, a partir de 2 registros no ano. A regra fica numa constante só (`LIMITE_OUTLIER` em `comprasAnual.ts`). Se o QA achar ruído demais, subir o mínimo de registros é uma linha. A decisão D11 fixa só os 20%.
- **SVG e foco.** O `:focus-visible` global (`index.css:266`) não desenha direito em `<path>`. Por isso o contorno sobreposto e o `outline: none` inline. Não reordene os paths ao fixar, porque o elemento focado perde o foco.
- **`url(#id)` com `useId`.** No React 19, o `useId` gera caracteres que precisam ser saneados antes de ir para `fill`, tanto no mapa quanto na hachura do Recharts.
- **Dados.** Os e2e de Compras dependem do registro de R$ 22,7 bi de 2025 (texto "1 registro"). Se a UFMG corrigir a base, esse assert muda junto.
- **Bundle.** `PeriodoAnos`, `BotaoAplicar`, `Alternador`, `escalaMapa` e `ChoroplethLegend` só podem ser importados pelas páginas. Se o `check:bundle` subir, confira com `grep -n "ui/" src/App.tsx src/ui/AppShell.tsx src/rotas.ts`.

### Critical Files for Implementation
- /Users/allansene/Repos/dadosfera/project-embrapii-busca/Dashboard/backend/api/compras.py
- /Users/allansene/Repos/dadosfera/project-embrapii-busca/Dashboard/frontend/src/components/MapaBrasil.tsx
- /Users/allansene/Repos/dadosfera/project-embrapii-busca/Dashboard/frontend/src/pages/Compras.tsx
- /Users/allansene/Repos/dadosfera/project-embrapii-busca/Dashboard/frontend/src/pages/Leitos.tsx
- /Users/allansene/Repos/dadosfera/project-embrapii-busca/Dashboard/frontend/e2e/smoke.spec.ts
