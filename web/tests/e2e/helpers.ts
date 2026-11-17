import { expect, type Page } from "@playwright/test";

export const viewports = [
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1024x768", width: 1024, height: 768 },
  { name: "768x1024", width: 768, height: 1024 },
  { name: "390x844", width: 390, height: 844 },
  { name: "360x800", width: 360, height: 800 },
] as const;

export async function openMap(page: Page) {
  await page.goto("mapa/");
  await expect(page.locator("#map canvas")).toBeVisible();
  await expect(page.locator("#map")).toHaveAttribute("data-ready", "true");
}

export async function openMaqueta(page: Page) {
  await page.goto("maqueta/");
  await expect(page.locator("#scene canvas")).toBeVisible();
  await expect(page.locator("#maqueta-stage")).toHaveClass(/is-loaded/, { timeout: 20_000 });
}

export async function horizontalOverflow(page: Page) {
  return page.evaluate(() => {
    const root = document.documentElement;
    return {
      scrollWidth: root.scrollWidth,
      clientWidth: root.clientWidth,
    };
  });
}

export function overlaps(
  a: { x: number; y: number; width: number; height: number },
  b: { x: number; y: number; width: number; height: number },
  tolerance = 1,
) {
  return !(
    a.x + a.width <= b.x + tolerance ||
    a.x >= b.x + b.width - tolerance ||
    a.y + a.height <= b.y + tolerance ||
    a.y >= b.y + b.height - tolerance
  );
}
