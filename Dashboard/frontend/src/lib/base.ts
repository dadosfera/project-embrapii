declare global {
  interface Window {
    __APP_BASE__?: string;
  }
}

/** Prefixo do app ("" local, "/pbp-service-…_8000" no Orchest), injetado pelo FastAPI. */
export const APP_BASE: string = (window.__APP_BASE__ ?? "").replace(/\/$/, "");

// Quando o FastAPI injeta window.__APP_BASE__ (build servido por ele), o prefixo em
// runtime manda: ignora VITE_API_URL para não escapar do proxy/prefixo do Orchest.
const API_ORIGIN: string =
  window.__APP_BASE__ !== undefined
    ? ""
    : (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

/** URL de um endpoint da API: apiUrl("/api/compras/kpis"). */
export function apiUrl(path: string): string {
  return `${API_ORIGIN || APP_BASE}${path}`;
}

/** URL de um arquivo de public/: assetUrl("maps/brasil-ufs.geojson"). */
export function assetUrl(path: string): string {
  return `${APP_BASE}/${path.replace(/^\//, "")}`;
}
