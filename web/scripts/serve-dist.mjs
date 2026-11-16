#!/usr/bin/env node
// Sirve dist/ para Playwright respetando BASE_PATH (GitHub Pages).
// Uso: BASE_PATH=/rio-piura-atlas node scripts/serve-dist.mjs
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "dist");
const base = (process.env.BASE_PATH ?? "").replace(/\/$/, "");
const port = Number(process.env.PORT ?? 4322);

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
  ".wasm": "application/wasm",
};

async function resolveFile(urlPath) {
  let clean = decodeURIComponent(urlPath.split("?")[0]);
  if (base && (clean === base || clean.startsWith(`${base}/`))) {
    clean = clean.slice(base.length) || "/";
  } else if (base) {
    return null;
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

server.listen(port, "127.0.0.1", () => {
  console.log(`sirviendo ${root} en http://127.0.0.1:${port}${base || "/"}`);
});
