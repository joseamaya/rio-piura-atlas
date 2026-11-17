import { expect, test } from "@playwright/test";
import { horizontalOverflow, viewports } from "./helpers";

const pages = [
  { route: "/", name: "inicio" },
  { route: "/mapa/", name: "mapa" },
  { route: "/escenarios/", name: "escenarios" },
  { route: "/fuentes/", name: "fuentes" },
  { route: "/maqueta/", name: "maqueta" },
] as const;

async function settle(page: import("@playwright/test").Page, route: string) {
  // BASE_PATH puede ser /rio-piura-atlas en CI: una ruta absoluta se saltaría
  // el subdirectorio. Las rutas relativas respetan el baseURL de Playwright.
  await page.goto(route === "/" ? "./" : route.replace(/^\/+/, ""));
  if (route === "/mapa/") {
    await expect(page.locator("#map")).toHaveAttribute("data-ready", "true");
  }
  if (route === "/maqueta/") {
    await expect(page.locator("#maqueta-stage")).toHaveClass(/is-loaded/, { timeout: 20_000 });
  }
}

test.describe("responsive · cinco resoluciones", () => {
  for (const viewport of viewports) {
    for (const target of pages) {
      test(`${target.name} · ${viewport.name}`, async ({ page }) => {
        const errors: string[] = [];
        page.on("pageerror", (error) => errors.push(String(error)));
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await settle(page, target.route);

        const { scrollWidth, clientWidth } = await horizontalOverflow(page);
        expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);

        if (target.route === "/mapa/") {
          const sizes = await page.evaluate(() => {
            const canvas = document.querySelector<HTMLCanvasElement>("#map canvas");
            const container = document.querySelector<HTMLElement>("#map");
            if (!canvas || !container) return null;
            const c = canvas.getBoundingClientRect();
            const w = container.getBoundingClientRect();
            return { canvas: [c.width, c.height], container: [w.width, w.height] };
          });
          expect(sizes).not.toBeNull();
          if (sizes) {
            expect(Math.abs(sizes.canvas[0] - sizes.container[0])).toBeLessThanOrEqual(2);
            expect(Math.abs(sizes.canvas[1] - sizes.container[1])).toBeLessThanOrEqual(2);
            expect(sizes.canvas[0]).toBeGreaterThan(0);
            expect(sizes.canvas[1]).toBeGreaterThan(0);
          }

          const controls = await page.locator(".map-controls").boundingBox();
          expect(controls).not.toBeNull();
          if (controls) {
            expect(controls.x).toBeGreaterThanOrEqual(0);
            expect(controls.y).toBeGreaterThanOrEqual(0);
            expect(controls.x + controls.width).toBeLessThanOrEqual(viewport.width + 1);
            expect(controls.y + controls.height).toBeLessThanOrEqual(viewport.height + 1);
          }

          if (viewport.width <= 900) {
            const toggle = page.locator("#toggle-panel");
            await expect(toggle).toBeVisible();
            const toggleBox = await toggle.boundingBox();
            expect(toggleBox).not.toBeNull();
            if (toggleBox) {
              expect(toggleBox.x).toBeGreaterThanOrEqual(0);
              expect(toggleBox.x + toggleBox.width).toBeLessThanOrEqual(viewport.width + 1);
            }
            await expect(page.locator("#legend-toggle")).toBeVisible();

            await toggle.click();
            await expect(page.locator(".map-panel")).toHaveAttribute("role", "dialog");
            await expect(page.locator("#panel-close")).toBeVisible();
            await page.keyboard.press("Escape");
            await expect(page.locator(".map-panel")).toHaveClass(/collapsed/);
          } else {
            await expect(page.locator(".map-panel")).toBeVisible();
          }
        }

        if (target.route === "/maqueta/") {
          const sizes = await page.evaluate(() => {
            const canvas = document.querySelector<HTMLCanvasElement>("#scene canvas");
            const container = document.querySelector<HTMLElement>("#scene");
            if (!canvas || !container) return null;
            const c = canvas.getBoundingClientRect();
            const w = container.getBoundingClientRect();
            return { canvas: [c.width, c.height], container: [w.width, w.height] };
          });
          expect(sizes).not.toBeNull();
          if (sizes) {
            expect(Math.abs(sizes.canvas[0] - sizes.container[0])).toBeLessThanOrEqual(2);
            expect(Math.abs(sizes.canvas[1] - sizes.container[1])).toBeLessThanOrEqual(2);
            expect(sizes.canvas[0]).toBeGreaterThan(0);
            expect(sizes.canvas[1]).toBeGreaterThan(0);
          }
        }

        expect(errors).toEqual([]);
      });
    }
  }
});

test("orientación horizontal: mapa y maqueta redimensionan sus canvas", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await settle(page, "/mapa/");

  const before = await page.evaluate(() => {
    const canvas = document.querySelector<HTMLCanvasElement>("#map canvas");
    const container = document.querySelector<HTMLElement>("#map");
    return {
      canvas: canvas ? [canvas.getBoundingClientRect().width, canvas.getBoundingClientRect().height] : null,
      container: container
        ? [container.getBoundingClientRect().width, container.getBoundingClientRect().height]
        : null,
    };
  });
  expect(before.canvas).not.toBeNull();

  await page.setViewportSize({ width: 844, height: 390 });
  await expect
    .poll(async () =>
      page.evaluate(() => {
        const canvas = document.querySelector<HTMLCanvasElement>("#map canvas");
        const container = document.querySelector<HTMLElement>("#map");
        if (!canvas || !container) return false;
        const c = canvas.getBoundingClientRect();
        const w = container.getBoundingClientRect();
        return Math.abs(c.width - w.width) <= 2 && Math.abs(c.height - w.height) <= 2;
      }),
    )
    .toBe(true);

  const overflow = await horizontalOverflow(page);
  expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.clientWidth + 1);

  await page.setViewportSize({ width: 390, height: 844 });
  await settle(page, "/maqueta/");
  await page.setViewportSize({ width: 844, height: 390 });
  await expect
    .poll(async () =>
      page.evaluate(() => {
        const canvas = document.querySelector<HTMLCanvasElement>("#scene canvas");
        const container = document.querySelector<HTMLElement>("#scene");
        if (!canvas || !container) return false;
        const c = canvas.getBoundingClientRect();
        const w = container.getBoundingClientRect();
        return Math.abs(c.width - w.width) <= 2 && Math.abs(c.height - w.height) <= 2;
      }),
    )
    .toBe(true);
});
