import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const ROTAS = ["", "medicamentos", "compras", "leitos", "mapa", "fornecedores"];
const LARGURAS = [1440, 390];

async function semViolacoesGraves(page: Page) {
  // Espera transições CSS finitas terminarem: um botão saindo de disabled (opacity-50, transition-all)
  // lido no meio do fade dá falso color-contrast. Animações infinitas (skeleton) não bloqueiam.
  await page.waitForFunction(() =>
    document.getAnimations().every((a) => a.playState !== "running" || a.effect?.getComputedTiming().endTime === Infinity),
  );
  const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const graves = r.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(
    graves.map((v) => `${v.id}: ${v.nodes.length} nós — ${v.help} — ${v.nodes.slice(0, 3).map((n) => `${n.target.join(" ")} [${n.any.map((c) => c.message).join(";")}] ${n.html.slice(0, 160)}`).join(" | ")}`),
  ).toEqual([]);
}

// Estados que só aparecem depois de interação (os mesmos do smoke.spec.ts).
const INTERACOES: Record<string, (page: Page) => Promise<void>> = {
  medicamentos: async (page) => {
    await page.getByPlaceholder("ex: dipirona, insulina, seringa...").fill("dipirona");
    await page.getByRole("button", { name: "Buscar", exact: true }).click();
    const select = page.getByLabel("Selecione o item");
    await select.waitFor({ state: "visible" });
    await select.selectOption({ index: 1 });
    const resumo = page.waitForResponse((r) => r.url().includes("/api/medicamentos/") && r.url().includes("/resumo"));
    await page.getByRole("button", { name: "Pesquisar" }).click();
    await resumo;
    // Estado carregado (o mesmo que o smoke confere): botão de volta a "Pesquisar" e KPI com valor.
    await expect(page.getByRole("button", { name: "Pesquisar" })).toBeEnabled({ timeout: 60_000 });
    await expect(
      page.locator("article").filter({ has: page.getByText("Preço médio de compra", { exact: true }) }).locator("p").last(),
    ).toContainText("R$");
  },
  compras: async (page) => {
    await page.getByLabel("Data inicial").fill("2015-01-01");
    await page.getByLabel("Data final").fill("2024-12-31");
    const kpis = page.waitForResponse((r) => r.url().includes("/api/compras/kpis"));
    await page.getByRole("button", { name: "Pesquisar" }).click();
    await kpis;
    await expect(page.getByRole("button", { name: "Pesquisar" })).toBeEnabled({ timeout: 60_000 });
    await expect(
      page.locator("article").filter({ has: page.getByText("Valor total comprado", { exact: true }) }).locator("p").last(),
    ).toContainText("R$");
  },
  mapa: async (page) => {
    await page.getByPlaceholder("Ex.: dipirona, insulina, seringa...").fill("dipirona");
    await page.getByRole("button", { name: "Localizar itens" }).click();
    const select = page.getByLabel("Item", { exact: true });
    await select.waitFor({ state: "visible" });
    await select.selectOption({ index: 1 });
    const estoque = page.waitForResponse((r) => r.url().includes("/api/medicamentos/") && r.url().includes("/estoque-por-uf"));
    await page.getByRole("button", { name: "Buscar", exact: true }).click();
    await estoque;
    await expect(page.locator("tbody tr").first()).toBeVisible();
  },
};

for (const largura of LARGURAS) {
  for (const rota of ROTAS) {
    test(`axe /${rota} @${largura}px`, async ({ page }) => {
      await page.setViewportSize({ width: largura, height: 900 });
      await page.goto(rota);
      await page.waitForLoadState("networkidle");
      await semViolacoesGraves(page);
    });
  }

  for (const [rota, interagir] of Object.entries(INTERACOES)) {
    test(`axe /${rota} com dados @${largura}px`, async ({ page }) => {
      await page.setViewportSize({ width: largura, height: 900 });
      await page.goto(rota);
      await page.waitForLoadState("networkidle");
      await interagir(page);
      await page.waitForLoadState("networkidle");
      await semViolacoesGraves(page);
    });
  }
}

test("link 'Pular para o conteúdo' é o primeiro foco e leva ao <main>", async ({ page }) => {
  await page.goto("compras");
  await page.waitForLoadState("networkidle");
  await page.keyboard.press("Tab");
  const pular = page.getByRole("link", { name: "Pular para o conteúdo" });
  await expect(pular).toBeFocused();
  await expect(pular).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page.locator("main#conteudo")).toBeFocused();
});
