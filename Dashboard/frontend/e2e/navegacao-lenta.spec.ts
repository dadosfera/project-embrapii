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

// Follow-up do QA à correção acima ("clica numa rota B ainda pendente, aperta Voltar para A já
// montada" não deve deixar a barra presa). A primeira tentativa dependia só do objeto `location`
// do react-router (key { aoRevelar }, sem key={pathname}) — mas voltar para uma entrada de
// histórico já visitada reaproveita o MESMO objeto `location` de antes (mesma referência): o
// conteúdo troca para o Início corretamente (confirmado com este teste), só que o efeito de
// <RotaRevelada>, que depende desse objeto para saber que "uma rota nova foi revelada", não
// dispara de novo — para o React, o valor não mudou. A barra ficava presa até o timeout de 15s
// mesmo com o conteúdo certo na tela.
//
// A correção final ouve `popstate` (evento nativo do navegador, disparado por Voltar/Avançar)
// separadamente, e limpa a pendência ali — não depende de o `location` "parecer" diferente.
test("Voltar para uma rota já montada, com a rota clicada ainda pendente, limpa a barra na hora (achado B4, follow-up) @slow", async ({
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

  const cdp = await page.context().newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });
  await cdp.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 200,
    downloadThroughput: (400 * 1024) / 8,
    uploadThroughput: (400 * 1024) / 8,
  });

  await page.goto("", { waitUntil: "domcontentloaded" });

  const linkLeitos = page.getByRole("link", { name: "Leitos" }).first();
  await linkLeitos.waitFor({ state: "visible" });
  // O Início precisa estar de fato montado (não só o header/nav, que é o chunk de entrada) antes
  // do clique, para "voltar" cair numa rota já revelada — o chunk da própria Home também está sob
  // o throttling, daí o prazo maior que os 500ms usados depois de qualquer clique.
  await expect(page.getByRole("heading", { level: 1 })).toContainText(/Explore os dados do projeto/, {
    timeout: 30_000,
  });

  await linkLeitos.click();

  const barra = page.locator("header").getByRole("status", { name: "Carregando página" });
  await expect(barra).toBeAttached({ timeout: 500 });

  // Volta para o Início com o chunk de Leitos ainda represado por `page.route` — de propósito:
  // a barra tem que sumir sem depender dele nunca chegar.
  await page.goBack();

  await expect(barra).not.toBeAttached({ timeout: 500 });
  await expect(page.getByRole("heading", { level: 1 })).toContainText(/Explore os dados do projeto/);

  // Libera o chunk represado só para não deixar a rota pendurada no fim do teste.
  liberarChunkLeitos();
});
