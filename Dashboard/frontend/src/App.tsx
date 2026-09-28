import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router";

import { AppShell } from "./ui/AppShell";

const Home = lazy(() => import("./pages/Home").then((m) => ({ default: m.Home })));
const Medicamentos = lazy(() => import("./pages/Medicamentos").then((m) => ({ default: m.Medicamentos })));
const Compras = lazy(() => import("./pages/Compras").then((m) => ({ default: m.Compras })));
const Leitos = lazy(() => import("./pages/Leitos").then((m) => ({ default: m.Leitos })));
const Mapa = lazy(() => import("./pages/Mapa").then((m) => ({ default: m.Mapa })));
const Fornecedores = lazy(() => import("./pages/Fornecedores").then((m) => ({ default: m.Fornecedores })));

function Carregando() {
  return (
    <div className="mx-auto max-w-[1440px] space-y-4 px-4 py-8 md:px-8" role="status" aria-busy="true" aria-label="Carregando página">
      {/* Mesmo visual do <Skeleton>, sem cn()/tailwind-merge no chunk de entrada. */}
      <div className="h-10 w-72 animate-pulse rounded-md bg-subtle" />
      <div className="h-32 w-full animate-pulse rounded-md bg-subtle" />
      <div className="h-64 w-full animate-pulse rounded-md bg-subtle" />
    </div>
  );
}

export default function App() {
  return (
    <AppShell>
      <Suspense fallback={<Carregando />}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/medicamentos" element={<Medicamentos />} />
          <Route path="/compras" element={<Compras />} />
          <Route path="/leitos" element={<Leitos />} />
          <Route path="/mapa" element={<Mapa />} />
          <Route path="/fornecedores" element={<Fornecedores />} />
        </Routes>
      </Suspense>
    </AppShell>
  );
}
