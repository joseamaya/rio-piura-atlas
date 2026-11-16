const rawBase = import.meta.env.BASE_URL;
const base = rawBase.endsWith("/") ? rawBase : `${rawBase}/`;

/**
 * Convierte una ruta del atlas en una URL válida bajo el `base` de Astro.
 * En local (base "/") devuelve la misma ruta; en Pages añade /rio-piura-atlas.
 */
export function withBase(path: string): string {
  if (!path || path === "/") return base;
  return `${base.replace(/\/$/, "")}/${path.replace(/^\//, "")}`;
}
