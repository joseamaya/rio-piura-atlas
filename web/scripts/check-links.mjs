#!/usr/bin/env node
// Comprueba enlaces internos y anclas sobre el sitio ya compilado (dist/).
// Sin dependencias: solo Node.

import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "dist");
const base = (process.env.BASE_PATH ?? "").replace(/\/$/, "");

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...(await walk(full)));
    else if (entry.name.endsWith(".html")) files.push(full);
  }
  return files;
}

function extract(html) {
  const ids = new Set();
  for (const match of html.matchAll(/\sid="([^"]+)"/g)) ids.add(match[1]);
  const links = [];
  for (const match of html.matchAll(/<a\b[^>]*\shref="([^"]*)"/g)) links.push(match[1]);
  return { ids, links };
}

async function resolveTarget(candidate) {
  const options = candidate.endsWith("/")
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

const idCache = new Map();
async function anchorsOf(file) {
  if (!idCache.has(file)) {
    const html = await readFile(file, "utf8");
    idCache.set(file, extract(html).ids);
  }
  return idCache.get(file);
}

const problems = [];
let checked = 0;

for (const page of await walk(root)) {
  const html = await readFile(page, "utf8");
  const { ids, links } = extract(html);
  const pageUrl = `/${path.relative(root, page).replaceAll(path.sep, "/")}`;

  for (const href of links) {
    if (!href || /^(https?:|mailto:|tel:|javascript:|data:|\/\/)/i.test(href)) continue;
    checked += 1;

    const [beforeHash, rawHash = ""] = href.split("#");
    let pathname = beforeHash.split("?")[0];
    if (base && (pathname === base || pathname.startsWith(`${base}/`))) {
      pathname = pathname.slice(base.length) || "/";
    }
    const hash = rawHash ? decodeURIComponent(rawHash) : "";

    let targetFile;
    if (!pathname) {
      targetFile = page;
    } else {
      const targetPath = pathname.startsWith("/")
        ? path.join(root, pathname)
        : path.resolve(path.dirname(page), pathname);
      targetFile = await resolveTarget(targetPath);
      if (!targetFile) {
        problems.push(`${pageUrl}: enlace roto -> ${href}`);
        continue;
      }
    }

    if (hash) {
      const targetIds = targetFile === page ? ids : await anchorsOf(targetFile);
      if (!targetIds.has(hash)) {
        problems.push(`${pageUrl}: ancla inexistente -> ${href}`);
      }
    }
  }
}

if (problems.length) {
  console.error(`enlaces: ${problems.length} problema(s) de ${checked} comprobados`);
  for (const problem of problems) console.error(`  - ${problem}`);
  process.exit(1);
}

console.log(`enlaces: ${checked} internos comprobados, sin roturas`);
