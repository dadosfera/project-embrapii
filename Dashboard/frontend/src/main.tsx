import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";

import App from "./App";
import "./index.css";
import { APP_BASE } from "./lib/base";

createRoot(
  document.getElementById("root")!,
).render(
  <StrictMode>
    <BrowserRouter basename={APP_BASE || "/"}>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
