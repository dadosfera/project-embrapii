import { defineConfig } from "@playwright/test";

// O baseURL sempre termina em "/": as rotas do smoke não têm barra inicial, então o
// Playwright resolve dentro do prefixo do Orchest quando E2E_BASE_URL já traz um
// (ex.: http://localhost:8000/pbp-test_8000).
function comBarraFinal(url: string): string {
  return url.endsWith("/") ? url : `${url}/`;
}

export default defineConfig({
  testDir: "e2e",
  timeout: 90_000,
  use: { baseURL: comBarraFinal(process.env.E2E_BASE_URL ?? "http://localhost:8000/") },
});
