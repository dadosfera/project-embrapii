import { expect, test, type Page } from "@playwright/test";

// Prints do subprojeto C, para conferência visual manual (hachura em 2025, 27 UFs legíveis a
// 390px, painel do mapa embaixo do mapa a 390px, legenda sem quebra feia a 1024px). Marcado
// "@slow": test-results/ não é versionado (.gitignore do front), então os prints não entram
// no commit — só servem de evidência local, como no subprojeto B.

const LARGURAS = [1440, 1024, 390] as const;

/** Digita no seletor CATMAT e escolhe a opção cujo texto contém `opcao` (cmdk: role="option"). */
async function escolherCatmat(page: Page, campo: string, termo: string, opcao: string | RegExp) {
  await page.locator(campo).fill(termo);
  const item = page.getByRole("option").filter({ hasText: opcao }).first();
  await item.waitFor({ state: "visible", timeout: 60_000 });
  await item.click();
}

async function print(page: Page, pagina: string, largura: number) {
  await page.screenshot({
    fullPage: true,
    path: `test-results/prints-c/${pagina}-${largura}.png`,
  });
}

for (const largura of LARGURAS) {
  test(`prints de Compras @${largura}px @slow`, async ({ page }) => {
    await page.setViewportSize({ width: largura, height: 900 });
    await page.goto("compras");
    await page.waitForLoadState("networkidle");

    await expect(
      page.locator("article").filter({ has: page.getByText("Valor total comprado", { exact: true }) }).locator("p").last(),
    ).toContainText("R$", { timeout: 60_000 });

    await print(page, "compras", largura);
  });

  test(`prints de Leitos @${largura}px @slow`, async ({ page }) => {
    await page.setViewportSize({ width: largura, height: 900 });
    await page.goto("leitos");
    await page.waitForLoadState("networkidle");

    await expect(
      page.locator("article").filter({ has: page.getByText("Leitos gerais", { exact: true }) }).locator("p").last(),
    ).not.toHaveText(/^(0|sem dado)$/, { timeout: 60_000 });

    await print(page, "leitos", largura);

    await page.getByRole("tab", { name: "Evolução histórica" }).dispatchEvent("mousedown");
    await page.getByRole("tab", { name: "Evolução histórica" }).click();
    await expect(page.locator("#inicio-evolucao")).toBeVisible();
    await page.waitForLoadState("networkidle");

    await print(page, "leitos-evolucao", largura);
  });

  test(`prints do Mapa @${largura}px @slow`, async ({ page }) => {
    await page.setViewportSize({ width: largura, height: 900 });
    await page.goto("mapa");
    await page.waitForLoadState("networkidle");

    const estoque = page.waitForResponse((r) => r.url().includes("/estoque-por-uf") && r.url().includes("escopo=grupo"));
    await escolherCatmat(page, "#mapa-busca-catmat", "dipirona 500", "DIPIRONA SÓDICA, DOSAGEM:500 MG");
    await estoque;
    await page.waitForLoadState("networkidle");

    const mg = page.getByRole("button", { name: /\(MG\):/ });
    await mg.focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("aside")).toContainText("Minas Gerais");

    await print(page, "mapa-estoque", largura);

    await page.getByRole("tab", { name: "Leitos por estado" }).dispatchEvent("mousedown");
    const leitosPorUf = page.waitForResponse((r) => r.url().includes("/api/leitos/por-uf"));
    await page.getByRole("tab", { name: "Leitos por estado" }).click();
    await leitosPorUf;
    await page.waitForLoadState("networkidle");

    await print(page, "mapa-leitos", largura);
  });

  test(`prints de Fornecedores @${largura}px @slow`, async ({ page }) => {
    await page.setViewportSize({ width: largura, height: 900 });
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

    await print(page, "fornecedores", largura);
  });
}
