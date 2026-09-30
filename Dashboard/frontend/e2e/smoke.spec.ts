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
      await expect(page.getByRole("img", { name: /Mapa do Brasil/ })).toBeVisible();
    }

    expect(erros).toEqual([]);
  });
}

test("Medicamentos: busca dipirona, seleciona o primeiro item e carrega o resumo", async ({
  page,
  baseURL,
}) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("medicamentos");
  await page.getByPlaceholder("ex: dipirona, insulina, seringa...").fill("dipirona");
  await page.getByRole("button", { name: "Buscar", exact: true }).click();

  const select = page.getByLabel("Selecione o item");
  await select.waitFor({ state: "visible" });
  await select.selectOption({ index: 1 });

  const resumo = page.waitForResponse((r) => r.url().includes("/api/medicamentos/") && r.url().includes("/resumo"));
  await page.getByRole("button", { name: "Pesquisar" }).click();
  await resumo;
  await page.waitForLoadState("networkidle");

  await expect(page.locator("body")).not.toContainText("Não foi possível");
  // Confirma que o resumo trazido pela API chegou até a tela (KPI "Preço médio de compra").
  const kpiPreco = page
    .locator("article")
    .filter({ has: page.getByText("Preço médio de compra", { exact: true }) });
  await expect(kpiPreco.locator("p").last()).toContainText("R$");

  expect(erros).toEqual([]);
});

test("Mapa: busca dipirona, seleciona um item com estoque e carrega a tabela por UF", async ({
  page,
  baseURL,
}) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("mapa");
  await page.getByPlaceholder("Ex.: dipirona, insulina, seringa...").fill("dipirona");
  await page.getByRole("button", { name: "Localizar itens" }).click();

  const select = page.getByLabel("Item", { exact: true });
  await select.waitFor({ state: "visible" });
  // O 1º resultado da busca não tem estoque para nenhuma UF; o 2º tem.
  await select.selectOption({ index: 1 });

  const estoque = page.waitForResponse((r) => r.url().includes("/api/medicamentos/") && r.url().includes("/estoque-por-uf"));
  await page.getByRole("button", { name: "Buscar", exact: true }).click();
  await estoque;
  await page.waitForLoadState("networkidle");

  await expect(page.locator("body")).not.toContainText("Não foi possível");
  // Confirma que a resposta virou linhas reais na tabela de estoque por UF.
  await expect(page.locator("tbody tr").first()).toBeVisible();

  expect(erros).toEqual([]);
});

test("Compras: aplica filtros com dados conhecidos e carrega os KPIs", async ({ page, baseURL }) => {
  const erros = coletarErros(page, baseURL!, []);

  await page.goto("compras");

  // O padrão da página (último ano até hoje) cai num vazio da base histórica;
  // usa uma janela com compras conhecidas para exercitar o pipeline de verdade.
  await page.getByLabel("Data inicial").fill("2015-01-01");
  await page.getByLabel("Data final").fill("2024-12-31");

  const kpis = page.waitForResponse((r) => r.url().includes("/api/compras/kpis"));
  await page.getByRole("button", { name: "Pesquisar" }).click();
  await kpis;
  await page.waitForLoadState("networkidle");

  await expect(page.locator("body")).not.toContainText("Não foi possível");
  // Confirma que o KPI de valor total, alimentado pela resposta da API, renderizou.
  // (o texto exato evita casar com o card do gráfico "Valor total comprado por mês".)
  const kpiValorTotal = page
    .locator("article")
    .filter({ has: page.getByText("Valor total comprado", { exact: true }) });
  await expect(kpiValorTotal.locator("p").last()).toContainText("R$");

  expect(erros).toEqual([]);
});
