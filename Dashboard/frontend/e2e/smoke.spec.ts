import { expect, test } from "@playwright/test";

const ROTAS = ["", "medicamentos", "compras", "leitos", "mapa", "fornecedores"];

for (const rota of ROTAS) {
  test(`página /${rota} carrega sem erro`, async ({ page }) => {
    const erros: string[] = [];
    page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
    page.on("response", (r) => r.url().includes("/api/") && r.status() >= 400 && erros.push(`${r.status()} ${r.url()}`));
    await page.goto(rota);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).not.toContainText("Não foi possível");
    expect(erros).toEqual([]);
  });
}
