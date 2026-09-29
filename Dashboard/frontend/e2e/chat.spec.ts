import { expect, test } from "@playwright/test";

// Chat Autodrive com contexto de tela. Opt-in porque chama o LLM do Autodrive STG (~30–90 s por pergunta):
//   E2E_CHAT=1 E2E_BASE_URL=http://localhost:8765/pbp-test_8000/ npx playwright test e2e/chat.spec.ts
// Playwright atravessa o shadow root aberto do <autodrive-chat> com seletores CSS normais.

test.skip(!process.env.E2E_CHAT, "defina E2E_CHAT=1 para rodar (usa o LLM do Autodrive)");
test.setTimeout(240_000);

test("pergunta sobre o medicamento da tela e recebe gráfico", async ({ page }) => {
  const perguntas: unknown[] = [];
  page.on("request", (req) => {
    if (req.method() === "POST" && req.url().includes("/api/autodrive/proxy/") && req.url().endsWith("/ai-question")) {
      perguntas.push(req.postDataJSON());
    }
  });

  await page.goto("medicamentos");
  await page.locator("#busca-medicamento").fill("lamotrigina 100");
  await page.getByRole("option").filter({ hasText: "LAMOTRIGINA, DOSAGEM:100 MG" }).first().click({ timeout: 60_000 });
  await expect(page.locator('[data-chat-context="KPIs"]')).toBeVisible({ timeout: 90_000 });

  await page.locator(".ad-chat__launcher").click();
  const input = page.locator(".ad-chat__input");
  await expect(input).toBeVisible({ timeout: 30_000 });
  await input.fill("Em quais UFs esse medicamento tem mais estoque? Mostre em gráfico");
  await page.getByRole("button", { name: "Enviar" }).click();

  const resposta = page.locator(".ad-chat__message--assistant").last();
  await expect(page.locator(".ad-chat__chart-block").first()).toBeVisible({ timeout: 180_000 });
  await expect(resposta).not.toContainText("chart-plus-json");

  const payload = perguntas[0] as { ui_context?: Record<string, any> };
  expect(payload.ui_context?.screen).toBe("Medicamentos");
  expect(payload.ui_context?.selection?.descricao).toMatch(/LAMOTRIGINA/);
  expect(payload.ui_context?.visible_data?.estoque_por_uf?.length).toBeGreaterThan(0);
  expect(payload.ui_context?.page_text?.KPIs).toMatch(/Estoque total/);

  await page.screenshot({ path: "test-results/chat-medicamentos.png", fullPage: false });
  await page.locator(".ad-chat__chart-block").first().screenshot({ path: "test-results/chat-grafico.png" });
});
