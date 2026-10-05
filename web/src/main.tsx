import { QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";

import { createQueryClient } from "./api/queryClient";
import App from "./App";
import "./index.css";

const root = document.getElementById("root");
if (root === null) {
  throw new Error("No se encuentra el elemento #root de index.html.");
}

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={createQueryClient()}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
