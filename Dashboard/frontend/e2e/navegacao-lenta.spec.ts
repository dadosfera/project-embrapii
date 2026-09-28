import { expect, test } from "@playwright/test";

// Achado de QA B4: numa rede lenta, o primeiro clique num link do menu não dava nenhum feedback
// (a página antiga e o item de menu ativo antigo ficavam parados por ~12s até o chunk da rota
// nova terminar de baixar). A correção tem duas partes (ver App.tsx/AppShell.tsx/Navegacao.tsx):
//   1. pré-carregamento de todos os chunks de rota em ocioso + no hover/foco do link do menu;
//   2. uma barra de progresso (aria-live) disparada por um estado de "navegação pendente" que
//      NÃO é um setState do próprio react-router (que embrulha a troca de localização num
//      startTransition e, por isso, não reexibe o Suspense fallback sobre o conteúdo já commitado).
//      A barra só aparece depois de ~150ms de pendência contínua (evita flicker/ruído de aria-live
//      em navegações já pré-carregadas), então o teste mira especificamente essa barra (dentro do
//      <header>) e não o skeleton do Suspense (que fica dentro do <main>, e é o outro elemento com
//      o mesmo texto acessível "Carregando página").
//
// O ponto (1) é justamente o que torna esse teste chato de simular de forma confiável: com CDP
// throttling sozinho, o pré-carregamento em ocioso corre uma corrida contra o clique e, boa parte
// das vezes, já baixou o chunk de Leitos antes do teste conseguir clicar (o próprio hover que o
// Playwright faz antes do clique já dispara o pré-carregamento por hover, ver Navegacao.tsx) —
// tornando o teste flaky pra qualquer lado. Para eliminar a corrida, além do throttling (que dá o
// cenário realista de rede lenta) o teste atrasa deliberadamente só a resposta do chunk de Leitos
// via `page.route`, garantindo que ele ainda não tenha chegado no instante do clique.
//
// Precisa de rede throttled via CDP (só Chromium) e de uma janela de tempo maior que o normal —
// por isso fica marcado "@slow" e fora do `npm run e2e` padrão (ver package.json: `e2e:slow`).
test("primeiro clique em Leitos, com rede throttled, mostra a barra de progresso em até ~500ms (achado B4) @slow", async ({
  page,
  browserName,
}) => {
  test.skip(browserName !== "chromium", "Network.emulateNetworkConditions via CDP só existe no Chromium");
  test.setTimeout(120_000);

  let liberarChunkLeitos: () => void = () => {};
  const chunkLeitosLiberado = new Promise<void>((resolve) => {
    liberarChunkLeitos = resolve;
  });
  await page.route("**/assets/Leitos-*.js", async (route) => {
    await chunkLeitosLiberado;
    await route.continue();
  });

  // Throttling antes da 1ª navegação (não só depois do DOM pronto): cenário realista de rede
  // lenta para o resto da página (fontes, outros chunks pré-carregados em ocioso etc.).
  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });
  await cdp.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 200,
    downloadThroughput: (400 * 1024) / 8, // ~400kbps: "regular 3G"
    uploadThroughput: (400 * 1024) / 8,
  });

  await page.goto("", { waitUntil: "domcontentloaded" });

  const linkLeitos = page.getByRole("link", { name: "Leitos" }).first();
  await linkLeitos.waitFor({ state: "visible" });

  const inicioClique = Date.now();
  await linkLeitos.click();

  // A barra (não o skeleton): role="status" com o nome acessível via aria-label, escopado ao
  // <header> — ver comentário acima. Prazo de 500ms = ~150ms de atraso proposital da barra +
  // margem, bem antes do chunk de Leitos (segurado por `page.route` até aqui) ser liberado.
  await expect(page.locator("header").getByRole("status", { name: "Carregando página" })).toBeAttached({
    timeout: 500,
  });

  const decorrido = Date.now() - inicioClique;
  expect(decorrido).toBeLessThan(500);

  // Libera o chunk represado: a navegação termina e a barra some.
  liberarChunkLeitos();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Leitos", { timeout: 100_000 });
});
