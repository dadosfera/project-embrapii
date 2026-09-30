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
  // "incomplete" = o axe não conseguiu decidir (ex.: fundo em gradiente). Vai para o relatório, não reprova.
  for (const v of r.incomplete) {
    test.info().annotations.push({ type: "axe-incomplete", description: `${v.id} (${v.impact ?? "?"}): ${v.nodes.length} nós` });
  }
  const graves = r.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
  expect(
    graves.map(
      (v) =>
        `${v.id}: ${v.nodes.length} nós — ${v.help} — ${v.nodes
          .slice(0, 3)
          .map((n) => `${n.target.join(" ")}: ${n.failureSummary ?? ""} ${n.html.slice(0, 160)}`)
          .join(" | ")}`,
    ),
  ).toEqual([]);
}

/** Digita no seletor CATMAT e escolhe a opção cujo texto contém `opcao` (cmdk: role="option"). */
async function escolherCatmat(page: Page, campo: string, termo: string, opcao: string | RegExp) {
  await page.locator(campo).fill(termo);
  const item = page.getByRole("option").filter({ hasText: opcao }).first();
  await item.waitFor({ state: "visible", timeout: 60_000 });
  await item.click();
}

// Estados que só aparecem depois de interação (os mesmos do smoke.spec.ts).
const INTERACOES: Record<string, (page: Page) => Promise<void>> = {
  medicamentos: async (page) => {
    const resumo = page.waitForResponse((r) => r.url().includes("/resumo") && r.url().includes("escopo=grupo"));
    await escolherCatmat(page, "#busca-medicamento", "dipirona 500", "DIPIRONA SÓDICA, DOSAGEM:500 MG");
    await resumo;
    await expect(
      page.locator("article").filter({ has: page.getByText("Preço médio de compra", { exact: true }) }).locator("p").last(),
    ).toContainText("R$");
  },
  compras: async (page) => {
    // A página abre carregada em 2020–2025, sem exigir clique: só espera o KPI.
    await expect(
      page.locator("article").filter({ has: page.getByText("Valor total comprado", { exact: true }) }).locator("p").last(),
    ).toContainText("R$", { timeout: 60_000 });
  },
  leitos: async (page) => {
    // Idem: carrega ao abrir com a competência mais recente.
    await expect(
      page.locator("article").filter({ has: page.getByText("Leitos gerais", { exact: true }) }).locator("p").last(),
    ).not.toHaveText(/^(0|sem dado)$/, { timeout: 60_000 });
  },
  mapa: async (page) => {
    const estoque = page.waitForResponse((r) => r.url().includes("/estoque-por-uf") && r.url().includes("escopo=grupo"));
    await escolherCatmat(page, "#mapa-busca-catmat", "dipirona 500", "DIPIRONA SÓDICA, DOSAGEM:500 MG");
    await estoque;
    await expect(page.locator("tbody tr").first()).toBeVisible();
  },
  fornecedores: async (page) => {
    // Fixa uma UF pelo teclado (foco + Enter no mapa), como o usuário faria.
    const sp = page.getByRole("button", { name: /\(SP\):/ });
    await sp.waitFor({ state: "visible", timeout: 60_000 });
    await sp.focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("body")).toContainText("Tabela filtrada por SP");
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

test("menu mobile @390px: abre, passa no axe, Escape devolve o foco, link navega e fecha", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("");
  await page.waitForLoadState("networkidle");

  const botao = page.getByRole("button", { name: "Abrir menu" });
  await botao.click();
  const menu = page.getByRole("dialog", { name: "Navegação" });
  await expect(menu).toBeVisible();
  await semViolacoesGraves(page);

  await page.keyboard.press("Escape");
  await expect(menu).toBeHidden();
  await expect(botao).toBeFocused();

  await botao.click();
  await expect(menu).toBeVisible();
  await menu.getByRole("link", { name: "Compras" }).click();
  await expect(menu).toBeHidden();
  await expect(page).toHaveURL(/\/compras$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Compras");
});
