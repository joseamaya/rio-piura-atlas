import { defineConfig } from "@playwright/test";

const basePath = (process.env.BASE_PATH ?? "").replace(/\/$/, "");
const origin = "http://127.0.0.1:4322";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: `${origin}${basePath || ""}/`,
    channel: "chrome",
    headless: true,
    launchOptions: {
      args: ["--no-sandbox", "--disable-dev-shm-usage", "--enable-unsafe-swiftshader"],
    },
  },
  webServer: {
    command: "node scripts/serve-dist.mjs",
    url: `${origin}${basePath || ""}/mapa/`,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
