import { defineConfig } from "@playwright/test";

// O baseURL sempre termina em "/": as rotas do smoke não têm barra inicial, então o
// Playwright resolve dentro do prefixo do Orchest quando E2E_BASE_URL já traz um
// (ex.: http://127.0.0.1:8000/pbp-test_8000). 127.0.0.1, não "localhost": em algumas máquinas
// "localhost" resolve primeiro para ::1, e outro serviço (ex.: um proxy do Docker Desktop) pode
// estar escutando ali na mesma porta.
function comBarraFinal(url: string): string {
  return url.endsWith("/") ? url : `${url}/`;
}

// Contra o data app publicado no Módulo de Inteligência, o Orchest exige o SSO da Dadosfera:
// E2E_STORAGE_STATE aponta para o JSON gerado por deploy/sso_storage_state.py (cookies ddf-*).
// Sem a variável, nada muda nas execuções locais.
const storageState = process.env.E2E_STORAGE_STATE || undefined;

export default defineConfig({
  testDir: "e2e",
  timeout: 90_000,
  use: {
    baseURL: comBarraFinal(process.env.E2E_BASE_URL ?? "http://127.0.0.1:8000/"),
    ...(storageState ? { storageState } : {}),
  },
});
