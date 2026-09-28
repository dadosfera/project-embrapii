import { expect, test } from "@playwright/test";

// Achado de QA B4: numa rede lenta, o primeiro clique num link do menu não dava nenhum feedback
// (a página antiga e o item de menu ativo antigo ficavam parados por ~12s até o chunk da rota
// nova terminar de baixar). A correção tem duas partes (ver App.tsx/AppShell.tsx/Navegacao.tsx):
//   1. pré-carregamento de todos os chunks de rota em ocioso + no hover/foco do link do menu;
//   2. uma barra de progresso (aria-live) disparada por um estado de "navegação pendente" que
//      NÃO é um setState do próprio react-router (que embrulha a troca de localização num
//      startTransition e, por isso, não reexibe o Suspense fallback sobre o conteúdo já commitado).
//
// Este teste simula a rede lenta antes do pré-carregamento em ocioso ter chance de rodar,
// clica em "Leitos" e confirma que algum feedback (skeleton do Suspense OU a barra/aria-live)
// aparece em até 300ms — bem antes do chunk (propositalmente lento) terminar de chegar.
test("primeiro clique em Leitos, com rede throttled, mostra feedback em até 300ms (achado B4)", async ({
  page,
  browserName,
}) => {
  test.skip(browserName !== "chromium", "Network.emulateNetworkConditions via CDP só existe no Chromium");
  test.setTimeout(120_000);

  // Throttling antes da 1ª navegação (não só depois do DOM pronto): senão o requestIdleCallback
  // do pré-carregamento, correndo ainda em rede rápida, baixa o chunk de Leitos antes do CDP
  // conseguir throttlear, e o clique não encontraria mais nada "por carregar".
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });
  await cdp.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 200,
    downloadThroughput: (400 * 1024) / 8, // ~400kbps: "regular 3G", devagar o bastante para o
    uploadThroughput: (400 * 1024) / 8, // chunk de Leitos não chegar em menos de 300ms.
  });

  await page.goto("", { waitUntil: "domcontentloaded" });

  const linkLeitos = page.getByRole("link", { name: "Leitos" }).first();
  await linkLeitos.waitFor({ state: "visible" });

  const inicioClique = Date.now();
  await linkLeitos.click();

  // Feedback aceito: o skeleton do Suspense (role="status" aria-label="Carregando página") OU
  // a barra de progresso da AppShell (role="status", mesmo texto via aria-live). Os dois têm
  // esse nome acessível.
  await expect(page.getByRole("status", { name: "Carregando página" }).first()).toBeAttached({
    timeout: 300,
  });

  const decorrido = Date.now() - inicioClique;
  expect(decorrido).toBeLessThan(300);

  // A navegação eventualmente termina (o teste não trava esperando a rede lenta acabar).
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Leitos", { timeout: 100_000 });
});
