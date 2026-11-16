import { expect, test } from "@playwright/test";

test.describe("mapa 2D", () => {
  test("carga capas, inunda y cierra el corte devolviendo el foco", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(String(error)));

    await page.goto("mapa/");
    await expect(page.locator("#map canvas")).toBeVisible();
    await expect(page.locator('[data-layer="cuenca"]')).toBeChecked();

    await page.locator('[data-layer="flood"]').check();
    await expect(page.locator("#layer-status")).toContainText("Mancha 2017");

    await page.locator(".cortes-list summary").click();
    const corte = page.locator(".corte-link").first();
    await corte.click();
    await expect(page.locator("#corte-panel")).toBeVisible();
    await expect(page.locator("#corte-chart svg")).toBeVisible();

    await page.locator("#corte-close").click();
    await expect(page.locator("#corte-panel")).toBeHidden();
    const active = await page.evaluate(() => document.activeElement?.className || "");
    expect(active).toContain("corte-link");
    expect(errors).toEqual([]);
  });

  test("muestra un aviso si falla una capa base y no deja el mapa en blanco", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    await page.route("**/data/cuenca.geojson", (route) => route.abort());
    await page.goto("mapa/");
    await expect(page.locator("#layer-status")).toContainText("No se pudieron cargar");
    await expect(page.locator("#map canvas")).toBeVisible();
    expect(errors).toEqual([]);
  });

  test("en móvil el panel arranca plegado y el mapa tiene área útil", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("mapa/");
    await expect(page.locator("#map canvas")).toBeVisible();
    await expect(page.locator(".map-panel")).toHaveClass(/collapsed/);
    const collapsed = await page.locator(".map-panel").boundingBox();
    expect(collapsed?.height ?? 0).toBeLessThan(130);

    await page.locator("#toggle-panel").click();
    await expect(page.locator(".map-panel")).not.toHaveClass(/collapsed/);
    const expanded = await page.locator(".map-panel").boundingBox();
    expect(expanded?.height ?? 0).toBeGreaterThan(180);
    await expect(page.locator("#toggle-panel")).toHaveText("Ocultar capas");
  });
});

test.describe("maqueta 3D", () => {
  test("carga el GLB y acepta teclado", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    await page.goto("maqueta/");
    await expect(page.locator("#scene canvas")).toBeVisible();
    await expect(page.locator("#scene-status")).toBeHidden();
    await expect(page.locator("#scene")).toHaveAttribute("tabindex", "0");
    await page.locator("#scene").focus();
    await page.keyboard.press("Home");
    await expect(page.locator("#reset-scene")).toBeVisible();
    expect(errors).toEqual([]);
  });
});
