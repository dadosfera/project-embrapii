import { expect, test, type Page } from "@playwright/test";

// Duas passagens são obrigatórias:
//   npm run e2e         -> baseURL "http://localhost:8000/" (backend sem APP_BASE_PATH)
//   npm run e2e:prefix  -> baseURL "http://localhost:8000/pbp-test_8000/" contra um backend
//                          iniciado com APP_BASE_PATH=/pbp-test_8000 (mesmo processo, só a env muda):
//                            APP_BASE_PATH=/pbp-test_8000 .venv/bin/uvicorn backend.main:app --port 8000
//                          Rode as duas contra o mesmo backend/tunnel, uma de cada vez.

const ROTAS: Array<{ rota: string; titulo: string | RegExp }> = [
  { rota: "", titulo: /Explore os dados do projeto/ },
  { rota: "medicamentos", titulo: /Medicamentos/ },
  { rota: "compras", titulo: /Compras/ },
  { rota: "leitos", titulo: /Leitos/ },
  { rota: "mapa", titulo: /Mapa do Brasil/ },
  { rota: "fornecedores", titulo: /Fornecedores/ },
];

// Requisições same-origin que o navegador dispara por conta própria e que o <base href>
// não alcança (ex.: favicon automático). Não são sinal de prefixo quebrado.
const IGNORAR_PREFIXO = ["/favicon.ico"];

function coletarErros(page: Page, baseURL: string, erros: string[]) {
  const origemEsperada = new URL(baseURL).origin;
  const prefixo = new URL(baseURL).pathname;

  page.on("console", (msg) => {
    if (msg.type() === "error") erros.push(`console.error: ${msg.text()}`);
  });

  page.on("pageerror", (err) => {
    erros.push(`pageerror: ${err.message}`);
  });

  page.on("request", (request) => {
    if (prefixo === "/") return; // sem prefixo configurado, nada a verificar

    const url = request.url();
    let mesmaOrigem = false;
    let pathname = "";
    try {
      const parsed = new URL(url);
      mesmaOrigem = parsed.origin === origemEsperada;
      pathname = parsed.pathname;
    } catch {
      mesmaOrigem = false;
    }

    if (mesmaOrigem && !IGNORAR_PREFIXO.includes(pathname) && !pathname.startsWith(prefixo)) {
      erros.push(`requisição sem o prefixo ${prefixo}: ${url}`);
    }
  });

  page.on("response", (response) => {
    const url = response.url();

    let mesmaOrigem = false;
    try {
      mesmaOrigem = new URL(url).origin === origemEsperada;
    } catch {
      mesmaOrigem = false;
    }

    if (mesmaOrigem && response.status() >= 400) {
      erros.push(`${response.status()} ${url}`);
    }

    const ehApi = url.includes("/api/");
    const ehGeojson = url.endsWith(".geojson");
    if (ehApi || ehGeojson) {
      const contentType = response.headers()["content-type"] ?? "";
      if (contentType.includes("text/html")) {
        erros.push(`content-type inesperado (text/html) em ${url}`);
      }
    }
  });

  return erros;
}

for (const { rota, titulo } of ROTAS) {
  test(`página /${rota} carrega sem erro`, async ({ page, baseURL }) => {
    const erros = coletarErros(page, baseURL!, []);

    await page.goto(rota);
    await page.waitForLoadState("networkidle");

    await expect(page.locator("body")).not.toContainText("Não foi possível");
    await expect(page.locator("#root")).not.toBeEmpty();
    await expect(page.getByRole("heading", { level: 1 })).toContainText(titulo);

    if (rota === "fornecedores") {
      // Fornecedores carrega o mapa por UF já no useEffect de montagem.
      // O mapa é um <svg role="group">, não uma <img> (ver MapaBrasil.tsx).
      await expect(page.getByRole("group", { name: /Mapa do Brasil/ })).toBeVisible();
    }

    expect(erros).toEqual([]);
  });
}

/** Digita no seletor CATMAT e escolhe a opção cujo texto contém `opcao` (cmdk: role="option"). */
async function escolherCatmat(page: Page, campo: string, termo: string, opcao: string | RegExp) {
  await page.locator(campo).fill(termo);
  const item = page.getByRole("option").filter({ hasText: opcao }).first();
  await item.waitFor({ state: "visible", timeout: 60_000 });
  await item.click();
}

test("Medicamentos: seletor agrupado soma as variantes, troca de código e mantém a seleção na URL", async ({
  page,
  baseURL,
}) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("medicamentos");
  const resumo = page.waitForResponse((r) => r.url().includes("/resumo") && r.url().includes("escopo=grupo"));
  await escolherCatmat(page, "#busca-medicamento", "dipirona 500", "DIPIRONA SÓDICA, DOSAGEM:500 MG");
  await resumo;
  await page.waitForLoadState("networkidle");

  await expect(page).toHaveURL(/catmat=BR0267203/);
  await expect(page.locator("body")).not.toContainText("Não foi possível");
  // Com as variantes somadas o item tem estoque (o código-base sozinho não tem nenhum).
  const kpiInst = page.locator("article").filter({ has: page.getByText("Instituições com registro", { exact: true }) });
  await expect(kpiInst.locator("p").last()).not.toHaveText(/^(0|sem dado)$/);
  const kpiPreco = page.locator("article").filter({ has: page.getByText("Preço médio de compra", { exact: true }) });
  await expect(kpiPreco.locator("p").last()).toContainText("R$");

  const todos = page.getByRole("radio", { name: /^Todos \(\d+\)/ });
  await expect(todos).toHaveAttribute("aria-checked", "true");
  await page.getByRole("radio", { name: /Componente Básico/ }).click();
  await expect(page).toHaveURL(/variante=BRBBR0267203U0042/);
  await page.waitForLoadState("networkidle");

  await page.reload();
  await expect(page.getByRole("radio", { name: /Componente Básico/ })).toHaveAttribute("aria-checked", "true");
  await page.goBack();
  await expect(page.getByRole("radio", { name: /^Todos/ })).toHaveAttribute("aria-checked", "true");

  expect(erros).toEqual([]);
});

test("Medicamentos: busca ignora acento e põe o princípio ativo antes das associações", async ({ page }) => {
  await page.goto("medicamentos");
  await page.locator("#busca-medicamento").fill("acido folico");
  const primeira = page.getByRole("option").first();
  await expect(primeira).toContainText(/ÁCIDO FÓLICO/, { timeout: 60_000 });
  await expect(page.getByRole("group", { name: "ÁCIDO FÓLICO", exact: true })).toBeVisible();
});

test("Medicamentos: link direto com ?catmat= abre o item", async ({ page }) => {
  await page.goto("medicamentos?catmat=BR0272809");
  await expect(page.locator("#busca-medicamento")).toHaveValue(/LAMOTRIGINA, DOSAGEM:100 MG/, { timeout: 60_000 });
  await expect(page.locator('[data-chat-context="KPIs"]')).toBeVisible({ timeout: 90_000 });
});

test("Mapa: escolhe dipirona 500 no seletor e carrega a tabela por UF", async ({
  page,
  baseURL,
}) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("mapa");
  const estoque = page.waitForResponse((r) => r.url().includes("/estoque-por-uf") && r.url().includes("escopo=grupo"));
  await escolherCatmat(page, "#mapa-busca-catmat", "dipirona 500", "DIPIRONA SÓDICA, DOSAGEM:500 MG");
  await estoque;
  await page.waitForLoadState("networkidle");

  await expect(page.locator("body")).not.toContainText("Não foi possível");
  await expect(page.locator("tbody tr").first()).toBeVisible();

  expect(erros).toEqual([]);
});

test("Leitos: abre carregado com o KPI e mostra 27 UFs e a evolução", async ({ page, baseURL }) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("leitos");
  await page.waitForLoadState("networkidle");

  await expect(page.locator("body")).not.toContainText("Não foi possível");
  const kpiLeitosGerais = page
    .locator("article")
    .filter({ has: page.getByText("Leitos gerais", { exact: true }) });
  await expect(kpiLeitosGerais.locator("p").last()).not.toHaveText(/^(0|sem dado)$/);

  // Aba "Distribuição por UF" já vem selecionada: 27 UFs no eixo Y.
  await expect(page.locator(".recharts-yAxis .recharts-cartesian-axis-tick")).toHaveCount(27);

  await page.getByRole("tab", { name: "Evolução histórica" }).dispatchEvent("mousedown");
  await page.getByRole("tab", { name: "Evolução histórica" }).click();
  await expect(page.locator("#inicio-evolucao")).toBeVisible();

  expect(erros).toEqual([]);
});

test("Mapa: aba Leitos por estado carrega sem clique, foco e Enter fixam MG", async ({ page, baseURL }) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("mapa");
  await page.waitForLoadState("networkidle");

  await page.getByRole("tab", { name: "Leitos por estado" }).dispatchEvent("mousedown");
  const leitosPorUf = page.waitForResponse((r) => r.url().includes("/api/leitos/por-uf"));
  await page.getByRole("tab", { name: "Leitos por estado" }).click();
  await leitosPorUf;
  await page.waitForLoadState("networkidle");

  await expect(page.locator("body")).not.toContainText("Não foi possível");

  const mg = page.getByRole("button", { name: /\(MG\):/ });
  await mg.focus();
  await page.keyboard.press("Enter");

  await expect(page.locator("aside")).toContainText("Minas Gerais");

  // A legenda traz a unidade da métrica exibida (padrão: "Participação do SUS (%)").
  await expect(page.getByText(/Legenda \(.*\)/)).toBeVisible();

  expect(erros).toEqual([]);
});

test("Fornecedores: clicar em SP no mapa filtra o ranking", async ({ page, baseURL }) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("fornecedores");
  await page.waitForLoadState("networkidle");

  await expect(page.getByRole("group", { name: /Mapa do Brasil/ })).toBeVisible();

  const ranking = page.waitForResponse(
    (r) => r.url().includes("/api/fornecedores/ranking") && r.url().includes("uf=SP"),
  );
  const sp = page.getByRole("button", { name: /\(SP\):/ });
  await sp.click();
  await ranking;
  await page.waitForLoadState("networkidle");

  await expect(page.locator("body")).toContainText("Tabela filtrada por SP");

  expect(erros).toEqual([]);
});

test("Fornecedores: busca por 'unique' filtra a tabela para uma única linha", async ({ page, baseURL }) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("fornecedores");
  await page.waitForLoadState("networkidle");

  await page.locator("#fornecedores-busca").fill("unique");
  const opcao = page.getByRole("option").first();
  await opcao.waitFor({ state: "visible", timeout: 60_000 });

  const ranking = page.waitForResponse(
    (r) => r.url().includes("/api/fornecedores/ranking") && r.url().includes("fornecedor_id="),
  );
  await opcao.click();
  await ranking;
  await page.waitForLoadState("networkidle");

  await expect(page.locator("tbody tr")).toHaveCount(1);

  expect(erros).toEqual([]);
});

test("Compras abre carregada em 2020–2025", async ({ page, baseURL }) => {
  const erros = coletarErros(page, baseURL!, []);

  const kpis = page.waitForResponse(
    (r) => r.url().includes("/api/compras/kpis") && r.url().includes("data_inicio=2020-01-01") && r.url().includes("data_fim=2025-12-31"),
  );
  await page.goto("compras");
  await kpis;
  await page.waitForLoadState("networkidle");

  await expect(page.locator("body")).not.toContainText("Não foi possível");
  const kpiValorTotal = page
    .locator("article")
    .filter({ has: page.getByText("Valor total comprado", { exact: true }) });
  await expect(kpiValorTotal.locator("p").last()).toContainText("R$");

  // Nota do outlier de 2025 (um único registro responde por >20% do valor do ano).
  await expect(page.locator("body")).toContainText("1 registro");

  expect(erros).toEqual([]);
});

test("Compras aplica ano e medicamento", async ({ page, baseURL }) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("compras");
  await page.waitForLoadState("networkidle");

  await page.locator("#compras-periodo-de").click();
  await page.getByRole("option", { name: "2021", exact: true }).click();

  await escolherCatmat(page, "#produto-compras", "lamotrigina 100", "LAMOTRIGINA, DOSAGEM:100 MG");

  const kpis = page.waitForResponse(
    (r) => r.url().includes("/api/compras/kpis") && r.url().includes("data_inicio=2021-01-01"),
  );
  await page.getByRole("button", { name: "Aplicar", exact: true }).click();
  await kpis;
  await page.waitForLoadState("networkidle");

  await expect(page.locator("body")).not.toContainText("Não foi possível");

  expect(erros).toEqual([]);
});

test("Compras: filtra por fornecedor e UF, KPIs carregam com fornecedor_id e uf", async ({ page, baseURL }) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("compras");
  await page.waitForLoadState("networkidle");

  await page.locator("#fornecedor-compras").fill("dimeva");
  const opcao = page.getByRole("option").filter({ hasText: "DIMEVA DISTRIBUIDORA" }).first();
  await opcao.waitFor({ state: "visible", timeout: 60_000 });
  await opcao.click();

  await page.locator("#uf-compras").click();
  await page.getByRole("option", { name: "MG", exact: true }).click();

  const kpis = page.waitForResponse(
    (r) => r.url().includes("/api/compras/kpis") && r.url().includes("uf=MG"),
  );
  await page.getByRole("button", { name: "Aplicar", exact: true }).click();
  const resposta = await kpis;
  await page.waitForLoadState("networkidle");

  expect(resposta.url()).toMatch(/fornecedor_id=\d+/);
  expect(resposta.url()).toContain("uf=MG");

  await expect(page.locator("body")).not.toContainText("Não foi possível");
  await expect(page.getByText(/Fornecedor:.*DIMEVA DISTRIBUIDORA/)).toBeVisible();
  await expect(page.getByText(/Estado:.*MG/)).toBeVisible();

  expect(erros).toEqual([]);
});

test("rota desconhecida (/nao-existe): mostra 'Página não encontrada' e um link para o Início (achado B3)", async ({
  page,
}) => {
  await page.goto("nao-existe");
  await page.waitForLoadState("networkidle");

  await expect(page.locator("body")).toContainText("Página não encontrada");
  await expect(page.locator("main#conteudo")).toBeVisible();

  const inicio = page.getByRole("link", { name: "Ir para o Início" });
  await expect(inicio).toBeVisible();
  await inicio.click();

  // Sem checar a URL: com prefixo (Orchest), o "/" da home não deixa a barra final na URL
  // (fica só ".../pbp-test_..."). O título da Home já confirma a navegação.
  await expect(page.getByRole("heading", { level: 1 })).toContainText(/Explore os dados do projeto/);
});
