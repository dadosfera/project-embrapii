/**
 * Carregadores das páginas lazy, num só lugar para não duplicar o `() => import(...)` entre o
 * `lazy()` do App.tsx e o pré-carregamento (ocioso + hover/foco no menu): dois `import("./pages/X")`
 * escritos em lugares diferentes viram dois chunks/dois pontos de manutenção.
 */
export const carregadoresDeRota = {
  "/": () => import("./pages/Home"),
  "/medicamentos": () => import("./pages/Medicamentos"),
  "/compras": () => import("./pages/Compras"),
  "/leitos": () => import("./pages/Leitos"),
  "/mapa": () => import("./pages/Mapa"),
  "/fornecedores": () => import("./pages/Fornecedores"),
} as const;

export type RotaConhecida = keyof typeof carregadoresDeRota;

/** Dispara o import() de uma rota. Falha é ignorada aqui: quem trata é a navegação real (Suspense/ChunkErrorBoundary). */
export function preCarregarRota(rota: RotaConhecida): void {
  carregadoresDeRota[rota]().catch(() => {
    /* a falha real aparece (e é tratada) quando a rota for de fato navegada */
  });
}

/** Pré-carrega todas as rotas. Uso: depois do primeiro paint, em ocioso (ver App.tsx). */
export function preCarregarTodasAsRotas(): void {
  (Object.keys(carregadoresDeRota) as RotaConhecida[]).forEach(preCarregarRota);
}
