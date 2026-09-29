# Subprojeto B: busca e agrupamento de CATMAT (+ padrão único de seleção)

**Data:** 29/09/2026 · **Branch:** `feat/dashboard-busca` (sobre `feat/dashboard-beast`) · **Achados do report de UX:** G6, G7, M1, M2, M3 (e o seletor CATMAT de Mapa e Compras)

## Status (29/09/2026)

As decisões da seção 3 foram tomadas pela opção recomendada. Os itens da seção 4 estão abaixo.

| Etapa | Status | Onde |
|---|---|---|
| 1. Backend: índice, `busca-agrupada`, `grupo/{chave}`, `?escopo=grupo` | Feito | `747fa0a`; `backend/catmat_index.py`, `backend/api/medicamentos.py` |
| 1b. Casos de grupo no teste de paridade Postgres × Snowflake | **Pendente**. Exige o túnel para o Postgres da UFMG, que é compartilhado; nele a flag de estoque fica `NULL` para não varrer a tabela de 39 GB | `tests/parity/cases.yaml` |
| 2. Front: `CatmatPicker`, chips de variante, estado na URL e estados vazios em Medicamentos; Mapa e Compras | Feito | `01682ed`; `components/CatmatPicker.tsx` |
| 3. `ui_context` do chat com item-base e códigos reunidos | Feito (`selection.item_base`, `selection.codigos_reunidos`, `filters.escopo`) | `pages/Medicamentos.tsx` |
| 4a. Testes locais: pytest, vitest, e2e smoke com prefixo | Feito: 127 · 57 · 12/12 | `backend/tests/test_catmat_index.py`, `e2e/smoke.spec.ts` |
| 4b. Prints em 1440 px e 390 px | Feito (conferência visual; não versionados) | — |
| 4c. Deploy no demo2 | Feito em 29/09 18:40, com `--skip-env-build` porque o Docker Hub segue devolvendo 429 no build do ambiente | `deploy/manifest.json` (`77b1097`) |
| 4d. Smoke e `chat.spec.ts` no publicado, com SSO | **Pendente** | `deploy/sso_storage_state.py` |
| 4e. PR `feat/dashboard-busca` | **Pendente** (depende do PR da `feat/dashboard-beast`) | — |

Em aberto fora do plano:
- Confirmar com a UFMG o que significam os prefixos B/E/S/O do BNAFAR. Hoje a UI mostra só "BNAFAR B", sem nome.
- Somar bases diferentes da mesma composição (seção 2.5).
- ~~O filtro de Compras continua com o botão "Pesquisar", que é do subprojeto C.~~ Resolvido no subprojeto C (30/09): Compras abre carregada em 2020–2025 e o filtro usa `BotaoAplicar` ("Aplicar"), igual a Leitos e Mapa.

## 1. Problema, com números do Snowflake (`EMBRAPII_DATASUS`)

A mesma coisa aparece várias vezes na busca, e cada cópia tem só uma parte dos dados.

| O que tem na base | Número |
|---|---|
| Itens CATMAT | 21.832 |
| Descrições repetidas (mesmo texto, códigos diferentes) | 1.463 descrições em 4.873 itens |
| Códigos-base `BR\d{7}` com mais de um item | 2.248 bases em 7.736 itens |
| Lixo (`INATIVO`, `TESTE`, `BR0000000`, sem descrição) | 854 itens |
| Itens com compra / com estoque | 11.143 / 15.413 |

Anatomia do código `BROBR0267203U0042`:

| Parte | Exemplo | Origem |
|---|---|---|
| Prefixo de componente | `BRO`, `BRB`, `BRE`, `BRS` | Só estoque, sistema BNAFAR (`WSBNDAF`); 617 mil posições. Hipótese a confirmar com a UFMG: B = Básico, E = Especializado, S = Estratégico, O = Outros |
| Código-base | `BR0267203` ("DIPIRONA SÓDICA, DOSAGEM:500 MG") | Todas as 263.562 compras estão em códigos-base puros |
| Unidade de fornecimento | `U0042` (comprimido) ou `-3` | Estoque HORUS (AF, ANTMICRO…) |

**Consequência:** dipirona 500 mg existe em cinco `catmat_id`. O preço está em `BR0267203`; o estoque está dividido entre `BR0267203U0042` (12.301 posições), `BRB…` (4.298), `BRO…` (50) e `BRS…` (19). Seja qual for o item escolhido, a tela mostra só uma parte, e o usuário não tem como saber. Além disso:

- a busca diferencia acento ("acido" traz 32 itens, "ácido" traz 200 e corta);
- a ordem é por byte, então associações aparecem antes do princípio ativo;
- chegar a um item leva três passos: digitar e Buscar, escolher num select, clicar Pesquisar.

## 2. Proposta

### 2.1 Três níveis
1. **Composição**, o título do grupo na lista de resultados. É o princípio ativo normalizado: o texto até a primeira vírgula ou número, sem acento. Exemplos: "ÁCIDO FÓLICO", "DIPIRONA SÓDICA + CAFEÍNA". O agrupamento é só visual; bases com códigos diferentes não são somadas.
2. **Item-base**, o que o usuário seleciona. É o código `BR\d{7}` com todas as variantes: apresentações `U…`/`-N` e componentes `BRB`/`BRE`/`BRS`/`BRO`. O nome é a descrição do código-base puro ou, se ele não existir, a descrição mais frequente do grupo. Códigos fora do padrão (`BRNT…` de nutrição, 471 itens) ficam como item-base próprio.
3. **Variante**, um refinamento opcional depois de selecionar. Chips mostram "Todas (5)", "Comprimido · U0042", "BNAFAR Básico"…

Protótipo em Python sobre a base real: 21.832 itens viram **16.306 itens-base**; "dipirona" cai de 68 para **29** resultados, com os de princípio ativo puro primeiro; "lamotrigina" fica com 8 itens e o de 100 mg reúne as 9 variantes.

### 2.2 Busca
- Sem acento, sem diferença de maiúsculas e espaços, e com ordem pt-BR.
- Ranking:
  1. código exato;
  2. nome começa com o termo;
  3. alguma variante começa com o termo;
  4. palavra dentro do texto.

  Dentro de cada faixa: princípio puro antes de associação, item com compras e estoque antes de item com só um dos dois, e item sem dado por último.
- **Implementação no backend:** um índice em memória carregado uma vez (21.832 linhas, cerca de 6,5 s no Snowflake, cache de 1 h). Não muda o esquema e vale igual para Postgres e Snowflake.
- **Endpoint novo `GET /api/medicamentos/busca-agrupada?q=`:** devolve até 30 itens-base agrupados por composição, com `base`, `nome`, `variantes[]`, `tem_compras` e `tem_estoque`.

### 2.3 Dados do item-base
- **Rotas existentes:** as `/api/medicamentos/{catmat_id}/…` ganham `?escopo=grupo`, que é o padrão da UI. Com ele, o filtro `produto.catmat_id = X` vira `IN (ids do grupo)`.
- **KPIs e estoque:** mantêm a regra atual, a última posição por instituição considerando todos os produtos do conjunto.
- **Compras:** passam a trazer as do código-base puro, de modo que preço e estoque aparecem juntos na mesma tela.
- **Variante:** com um chip de variante selecionado, a consulta usa `escopo=item` com o `catmat_id` da variante.
- **Testes de paridade:** Postgres × Snowflake ganham os casos de grupo.

### 2.4 Um seletor só (G6 no que toca CATMAT)
- **Componente `CatmatPicker`:** combobox com os componentes `Command` e `Popover`, que já existem em `components/ui`.
  - Filtra enquanto o usuário digita, com espera de 250 ms entre teclas.
  - Mostra os resultados agrupados por composição, cada linha com os selos "compras" e "estoque" e o número de variantes.
  - Funciona só pelo teclado.
- **Seleção carrega direto:** escolher um item já carrega os dados. Sem "Buscar" e sem "Pesquisar".
- **Mesmo componente em três páginas:** Medicamentos, Mapa e o filtro de medicamento de Compras.
- **Estado na URL** (`?catmat=BR0267203&variante=…`): voltar, recarregar e compartilhar o link mantêm a seleção. O chat Autodrive recebe o grupo e a variante no `ui_context`.
- **Estados vazios com causa:**
  - item sem estoque: "Este item não tem registro de estoque; veja as variantes" ou uma sugestão de item da mesma composição com dados;
  - valor nulo aparece como "sem dado", não como 0 (M2).

### 2.5 Fora deste subprojeto
- Somar bases diferentes da mesma composição (ex.: `BR0273824` + `BR0436731`, ambos "ácido fólico 2 mg"). Exige regra de equivalência de dose e forma e revisão da UFMG. Fica visível lado a lado, com os selos mostrando qual tem compras e qual tem estoque.
- O restante do C: Compras abrindo em 2020–2025, gráfico anual e botão "Aplicar" em Compras e Leitos.

## 3. Decisões para aprovar
1. **Escopo padrão = item-base inteiro**, com todas as variantes somadas e refinamento por chip. Alternativa: abrir no código exato escolhido.
2. **Lixo sai da busca**, com opção "incluir inativos" desligada por padrão.
3. **Itens sem dado aparecem por último** com o selo "sem dados", não escondidos.
4. **Composição agrupa só visualmente** (itens 2.1 e 2.5).
5. **Seletor único nas três páginas** e seleção na URL.

## 4. Ordem de execução (depois de aprovado)
1. Backend: `backend/catmat_index.py` (parser do código, normalização, ranking) com testes unitários sobre uma amostra real congelada, depois `busca-agrupada` e `escopo=grupo` com os testes de paridade.
2. Front: `CatmatPicker` + estado na URL + estados vazios em Medicamentos; depois Mapa e Compras.
3. `ui_context` do chat com grupo e variante.
4. QA: e2e (dipirona, ácido fólico, lamotrigina, item sem estoque, voltar/recarregar), prints 1440/1024/390, deploy no demo2 e smoke.
