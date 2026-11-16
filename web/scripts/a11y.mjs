#!/usr/bin/env node
// Auditoría WCAG A/AA con axe sobre el sitio compilado, en Chrome headless.
// Pensada para CI: usa chrome del sistema, sin descargar navegadores.

import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..", "dist");
const base = (process.env.BASE_PATH ?? "").replace(/\/$/, "");
const require = createRequire(import.meta.url);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".geojson": "application/geo+json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".png": "image/png",
  ".bin": "application/octet-stream",
  ".glb": "model/gltf-binary",
};

const pages = ["/", "/mapa/", "/maqueta/", "/escenarios/", "/fuentes/", "/404.html"].map(
  (route) => `${base}${route}`,
);

function chromePath() {
  const candidates = [
    process.env.CHROME_PATH,
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  ].filter(Boolean);
  return candidates.find((candidate) => existsSync(candidate)) ?? null;
}

async function resolveFile(urlPath) {
  let clean = decodeURIComponent(urlPath.split("?")[0]);
  if (base && (clean === base || clean.startsWith(`${base}/`))) {
    clean = clean.slice(base.length) || "/";
  }
  const candidate = path.join(root, clean);
  if (!candidate.startsWith(root)) return null;
  const options = clean.endsWith("/")
    ? [path.join(candidate, "index.html")]
    : [candidate, `${candidate}.html`, path.join(candidate, "index.html")];
  for (const option of options) {
    try {
      if ((await stat(option)).isFile()) return option;
    } catch {
      // siguiente candidato
    }
  }
  return null;
}

const server = createServer(async (req, res) => {
  const file = await resolveFile(req.url ?? "/");
  if (!file) {
    res.writeHead(404, { "content-type": "text/plain" });
    res.end("not found");
    return;
  }
  const body = await readFile(file);
  res.writeHead(200, { "content-type": MIME[path.extname(file)] ?? "application/octet-stream" });
  res.end(body);
});

await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const { port } = server.address();
const origin = `http://127.0.0.1:${port}`;

const executablePath = chromePath();
if (!executablePath) {
  console.error("No encuentro Chrome. Define CHROME_PATH para ejecutar la auditoría.");
  server.close();
  process.exit(1);
}

const axeSource = await readFile(require.resolve("axe-core/axe.min.js"), "utf8");

async function launchBrowser() {
  const args = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
  ];
  let lastError;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      return await puppeteer.launch({
        executablePath,
        headless: true,
        timeout: 60_000,
        protocolTimeout: 120_000,
        args,
      });
    } catch (error) {
      lastError = error;
      console.warn(`Chrome no arrancó (intento ${attempt}/3): ${error.message}`);
      await new Promise((resolve) => setTimeout(resolve, 2_000 * attempt));
    }
  }
  throw lastError;
}

const browser = await launchBrowser();

const violations = [];
try {
  for (const route of pages) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 900 });
    await page.goto(`${origin}${route}`, { waitUntil: "domcontentloaded", timeout: 45_000 });
    // Da tiempo a que el DOM dinámico (panel de cortes, capas) se monte.
    await new Promise((resolve) => setTimeout(resolve, 500));
    await page.addScriptTag({ content: axeSource });
    const result = await page.evaluate(() =>
      // @ts-expect-error axe se inyecta en la página
      window.axe.run(document, {
        runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
      }),
    );
    for (const violation of result.violations) {
      violations.push({ route, violation });
    }
    console.log(
      `${route}: ${result.violations.length} violación(es), ${result.passes.length} reglas correctas`,
    );
    await page.close();
  }
} finally {
  await browser.close();
  server.close();
}

if (violations.length) {
  console.error(`\naccesibilidad: ${violations.length} violación(es)`);
  for (const { route, violation } of violations) {
    const nodes = violation.nodes.map((node) => node.target.join(" ")).join(" | ");
    console.error(`  - ${route} [${violation.impact}] ${violation.id}: ${violation.help} (${nodes})`);
  }
  process.exit(1);
}

console.log("\naccesibilidad: sin violaciones WCAG A/AA");
