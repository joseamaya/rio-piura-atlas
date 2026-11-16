import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://example.org",
  base: "/",
  build: { inlineStylesheets: "auto" },
});
