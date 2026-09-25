// Prints do report de revisão de UX (docs/ux-review/index.html).
// Roda a partir de frontend/, contra o app local em Snowflake:
//   DB_ENGINE=snowflake .venv/bin/python -m uvicorn backend.main:app --port 8000   (em Dashboard/)
//   cd frontend && node ../docs/ux-review/capture.ts        (Node 23+; ou: npx tsx ../docs/ux-review/capture.ts)
// O Playwright é resolvido a partir de frontend/node_modules (cwd).
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(join(process.cwd(), "package.json"));
const { chromium } = require("@playwright/test");

const BASE = process.env.E2E_BASE_URL ?? "http://localhost:8000/";
// Segundo servidor com prefixo, para o teste da âncora: APP_BASE_PATH=/pbp-test_8000 ... --port 8001
const PREFIX_BASE = process.env.E2E_PREFIX_URL ?? "http://localhost:8001/pbp-test_8000/";
const OUT = join(dirname(fileURLToPath(import.meta.url)), "shots");
mkdirSync(OUT, { recursive: true });

const notas: Record<string, unknown> = {};

async function esperarFim(page: any) {
  await page.waitForLoadState("networkidle");
  await page.waitForFunction(
    () => !/Carregando|Buscando|Localizando/.test(document.body.innerText),
    null,
    { timeout: 120_000 },
  );
  await page.waitForTimeout(600);
}

async function shot(page: any, nome: string, fullPage = true) {
  await page.screenshot({ path: join(OUT, `${nome}.png`), fullPage });
  console.log("ok", nome);
}

async function cronometrar(page: any, acao: () => Promise<void>) {
  const t0 = Date.now();
  await acao();
  await esperarFim(page);
  return Date.now() - t0;
}

async function buscarMedicamento(page: any, termo: string, catmat: string, botaoBusca: string, botaoCarregar: string) {
  await page.getByPlaceholder(/dipirona, insulina/i).fill(termo);
  await page.getByRole("button", { name: botaoBusca, exact: true }).click();
  await esperarFim(page);
  await page.locator("select").first().selectOption(catmat);
  return cronometrar(page, () => page.getByRole("button", { name: botaoCarregar, exact: true }).click());
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: "light" });
  const page = await ctx.newPage();

  // 1. Estado padrão das 6 páginas
  for (const p of ["", "medicamentos", "compras", "leitos", "mapa", "fornecedores"]) {
    const t0 = Date.now();
    await page.goto(BASE + p);
    await esperarFim(page);
    notas[`carga_${p || "home"}_ms`] = Date.now() - t0;
    await shot(page, p || "home");
  }

  // 2. Medicamentos: primeiro resultado de "dipirona" (5176, sem estoque) e um item com dados (85)
  await page.goto(BASE + "medicamentos");
  await esperarFim(page);
  notas.med_5176_ms = await buscarMedicamento(page, "dipirona", "5176", "Buscar", "Pesquisar");
  await shot(page, "medicamentos-5176-vazio");
  await page.locator("select").first().selectOption("85");
  notas.med_85_ms = await cronometrar(page, () => page.getByRole("button", { name: "Pesquisar", exact: true }).click());
  await shot(page, "medicamentos-85");
  // lista de resultados: ordem que o usuário vê
  notas.med_opcoes = await page.locator("select#catmat option").evaluateAll((os: any[]) => os.slice(0, 6).map((o) => o.textContent));

  // 3. Compras: padrão (últimos 12 meses) e 2021
  await page.goto(BASE + "compras");
  await esperarFim(page);
  notas.compras_padrao_ms = await cronometrar(page, () => page.getByRole("button", { name: "Pesquisar", exact: true }).click());
  await shot(page, "compras-padrao-zerado");
  await page.fill("#data-inicio", "2020-01-01");
  await page.fill("#data-fim", "2025-12-31");
  notas.compras_2020_2025_ms = await cronometrar(page, () => page.getByRole("button", { name: "Pesquisar", exact: true }).click());
  await shot(page, "compras-2020-2025");
  await page.fill("#data-inicio", "2021-01-01");
  await page.fill("#data-fim", "2021-12-31");
  notas.compras_2021_ms = await cronometrar(page, () => page.getByRole("button", { name: "Pesquisar", exact: true }).click());
  await shot(page, "compras-2021");

  // 4. Leitos: aplicar filtros padrão
  await page.goto(BASE + "leitos");
  await esperarFim(page);
  notas.leitos_ms = await cronometrar(page, () => page.getByRole("button", { name: "Aplicar filtros", exact: true }).click());
  await shot(page, "leitos-aplicado");

  // 5. Mapa: 5176 (vazio), 85 (com dados) e aba de leitos
  await page.goto(BASE + "mapa");
  await esperarFim(page);
  notas.mapa_5176_ms = await buscarMedicamento(page, "dipirona", "5176", "Localizar itens", "Buscar");
  await shot(page, "mapa-5176-vazio");
  await page.locator("select").first().selectOption("85");
  notas.mapa_85_ms = await cronometrar(page, () => page.getByRole("button", { name: "Buscar", exact: true }).click());
  await shot(page, "mapa-85");
  await page.getByRole("tab", { name: "Leitos por estado" }).click();
  notas.mapa_leitos_ms = await cronometrar(page, () => page.getByRole("button", { name: "Buscar", exact: true }).click());
  await shot(page, "mapa-leitos");

  // 6. Larguras menores: 1024 (embed no Catálogo) e 390 (celular)
  for (const [w, h, sufixo] of [[1024, 768, "1024"], [390, 844, "390"]] as const) {
    const p2 = await (await browser.newContext({ viewport: { width: w, height: h } })).newPage();
    await p2.goto(BASE);
    await esperarFim(p2);
    await shot(p2, `home-${sufixo}`, false);
    await p2.goto(BASE + "medicamentos");
    await esperarFim(p2);
    await buscarMedicamento(p2, "dipirona", "85", "Buscar", "Pesquisar");
    await shot(p2, `medicamentos-85-${sufixo}`, false);
    await p2.goto(BASE + "compras");
    await esperarFim(p2);
    await p2.fill("#data-inicio", "2021-01-01");
    await p2.fill("#data-fim", "2021-12-31");
    await cronometrar(p2, () => p2.getByRole("button", { name: "Pesquisar", exact: true }).click());
    await shot(p2, `compras-2021-${sufixo}`);
    notas[`scroll_horizontal_${sufixo}`] = await p2.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    await p2.context().close();
  }

  // 7. Âncora #modulos sob o prefixo do Orchest: depois de voltar pelo "Início", recarrega o documento?
  await page.goto(PREFIX_BASE + "compras");
  await esperarFim(page);
  await page.getByRole("link", { name: "Início", exact: true }).click();
  await page.waitForTimeout(1000);
  notas.modulos_url_apos_inicio = page.url();
  await page.evaluate(() => ((window as any).__marca = 1));
  await page.getByRole("link", { name: "Ver módulos" }).click();
  await page.waitForTimeout(2500);
  notas.modulos_url = page.url();
  notas.modulos_recarregou = await page.evaluate(() => (window as any).__marca !== 1);

  writeFileSync(join(OUT, "notas.json"), JSON.stringify(notas, null, 2));
  console.log(notas);
  await browser.close();
})();
