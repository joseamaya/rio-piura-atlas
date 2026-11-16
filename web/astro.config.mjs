import { defineConfig } from "astro/config";

// El dominio definitivo se configura con SITE_URL al compilar.
// Mientras no exista despliegue, se mantiene un valor de ejemplo.
export default defineConfig({
  site: process.env.SITE_URL || "https://example.org",
  base: "/",
  build: { inlineStylesheets: "auto" },
});
