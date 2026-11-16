import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

// El dominio y el subdirectorio se configuran al compilar. En local se usan
// los valores raíz; el workflow de Pages inyecta SITE_URL y BASE_PATH.
const site = process.env.SITE_URL || "https://joseamaya.github.io";
const base = process.env.BASE_PATH || "/";

export default defineConfig({
  site,
  base,
  build: { inlineStylesheets: "auto" },
  integrations: [sitemap()],
});
