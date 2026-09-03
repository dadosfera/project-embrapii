import { Route, Routes } from "react-router";

import { Layout } from "./components/Layout";
import { Compras } from "./pages/Compras";
import { Home } from "./pages/Home";
import { Leitos } from "./pages/Leitos";
import { Mapa } from "./pages/Mapa";
import { Medicamentos } from "./pages/Medicamentos";
import { Fornecedores } from "./pages/Fornecedores";


export default function App() {
  return (
    <Layout>
      <Routes>
        <Route
          path="/"
          element={<Home />}
        />

        <Route
          path="/medicamentos"
          element={<Medicamentos />}
        />

        <Route
          path="/compras"
          element={<Compras />}
        />

        <Route
          path="/leitos"
          element={<Leitos />}
        />

        <Route
          path="/mapa"
          element={<Mapa />}
        />
        <Route
          path="/fornecedores"
          element={<Fornecedores />}
/>
      </Routes>
    </Layout>
  );
}