import { expect, test, type Page } from "@playwright/test";

async function openMap(page: Page) {
  await page.goto("mapa/");
  await expect(page.locator("#map canvas")).toBeVisible();
  await expect(page.locator("#map")).toHaveAttribute("data-ready", "true");
}

test.describe("mapa 2D", () => {
  test("carga capas, inunda y cierra el corte devolviendo el foco", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(String(error)));

    await openMap(page);
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

  test("dibuja un perfil topográfico con dos clics y declara su límite", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(String(error)));

    await openMap(page);
    await page.locator("#draw-corte").click();
    await expect(page.locator("#draw-corte")).toHaveAttribute("aria-pressed", "true");

    const box = await page.locator("#map").boundingBox();
    if (!box) throw new Error("sin caja del mapa");
    await page.mouse.click(box.x + box.width * 0.5, box.y + box.height * 0.5);
    await page.mouse.click(box.x + box.width * 0.65, box.y + box.height * 0.55);

    await expect(page.locator("#corte-title")).toHaveText("Corte dibujado");
    await expect(page.locator("#corte-chart svg")).toBeVisible();
    await expect(page.locator("#corte-note")).toContainText("~140 m");
    await expect(page.locator("#corte-note")).toContainText("no sirve para dimensionar obras");
    await expect(page.locator("#draw-corte")).toHaveAttribute("aria-pressed", "false");
    expect(errors).toEqual([]);
  });

  test("activa y desactiva las capas disponibles", async ({ page }) => {
    await openMap(page);

    for (const layer of ["cuenca", "subcuencas", "rios", "agua", "cortes"]) {
      const input = page.locator(`[data-layer="${layer}"]`);
      await expect(input).toBeChecked();
      await input.uncheck();
      await expect(input).not.toBeChecked();
      await input.check();
      await expect(input).toBeChecked();
    }

    const lugares = page.locator('[data-layer="lugares"]');
    const firstCity = page.locator(".city").first();
    await lugares.uncheck();
    await expect(firstCity).toHaveCSS("display", "none");
    await lugares.check();
    await expect(firstCity).not.toHaveCSS("display", "none");

    const obras = page.locator('[data-layer="obras"]');
    const firstObra = page.locator(".city.obra").first();
    await obras.check();
    await expect(firstObra).not.toHaveCSS("display", "none");
    await obras.uncheck();
    await expect(firstObra).toHaveCSS("display", "none");

    await page.locator('[data-layer="flood"]').check();
    await expect(page.locator("#layer-status")).toContainText("Mancha 2017");
    await page.locator('[data-layer="flood"]').uncheck();
    await expect(page.locator("#layer-status")).toHaveText("");
  });

  test("consulta la ficha de la cuenca desde el botón accesible", async ({ page }) => {
    await openMap(page);
    await page.locator("#ficha-cuenca").click();
    await expect(page.locator("#ficha")).toContainText("Cuenca del río Piura");
    await expect(page.locator("#ficha")).toContainText(/10[.,]938/);
    await expect(page.locator("#ficha")).toContainText("Shape_Area");
  });

  test("cierra el corte con Escape y devuelve el foco", async ({ page }) => {
    await openMap(page);
    await page.locator(".cortes-list summary").click();
    const corte = page.locator(".corte-link").first();
    await corte.click();
    await expect(page.locator("#corte-panel")).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(page.locator("#corte-panel")).toBeHidden();
    const active = await page.evaluate(() => document.activeElement?.className || "");
    expect(active).toContain("corte-link");
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

  test("avisa si falla la capa de inundación y deja el mapa operativo", async ({ page }) => {
    await page.route("**/data/flood_2017.geojson", (route) => route.abort());
    await openMap(page);
    const flood = page.locator('[data-layer="flood"]');
    await flood.click();
    await expect(page.locator("#layer-status")).toContainText(
      "No se pudo cargar la mancha de 2017",
    );
    await expect(flood).not.toBeChecked();
    await expect(page.locator("#map canvas")).toBeVisible();
  });

  test("en móvil el panel arranca plegado y el mapa tiene área útil", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("mapa/");
    await expect(page.locator("#map canvas")).toBeVisible();
    await expect(page.locator("#map")).toHaveAttribute("data-ready", "true");
    await expect(page.locator(".map-panel")).toHaveClass(/collapsed/);
    await expect(page.locator("#toggle-panel")).toHaveAttribute("aria-expanded", "false");
    const collapsed = await page.locator(".map-panel").boundingBox();
    expect(collapsed?.height ?? 0).toBeLessThan(130);

    await page.locator("#toggle-panel").click();
    await expect(page.locator(".map-panel")).not.toHaveClass(/collapsed/);
    await expect(page.locator("#toggle-panel")).toHaveAttribute("aria-expanded", "true");
    const expanded = await page.locator(".map-panel").boundingBox();
    expect(expanded?.height ?? 0).toBeGreaterThan(180);
    await expect(page.locator("#toggle-panel")).toHaveText("Ocultar capas");
  });
});

test.describe("maqueta 3D", () => {
  test("carga el GLB, reinicia la vista y acepta teclado", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    await page.goto("maqueta/");
    await expect(page.locator("#scene canvas")).toBeVisible();
    await expect(page.locator("#scene-status")).toBeHidden();
    await expect(page.locator("#scene")).toHaveAttribute("tabindex", "0");
    await page.locator("#scene").focus();
    await page.keyboard.press("Home");
    await expect(page.locator("#reset-scene")).toBeVisible();
    await page.locator("#reset-scene").click();
    expect(errors).toEqual([]);
  });

  test("si WebGL no está disponible muestra el enlace al mapa 2D", async ({ page }) => {
    await page.addInitScript(() => {
      const original = HTMLCanvasElement.prototype.getContext;
      (HTMLCanvasElement.prototype as any).getContext = function (
        type: string,
        ...args: any[]
      ) {
        if (String(type).includes("webgl")) return null;
        return (original as any).apply(this, [type, ...args]);
      };
    });
    await page.goto("maqueta/");
    const status = page.locator("#scene-status");
    await expect(status).toBeVisible();
    await expect(status).toContainText("WebGL");
    await expect(status.locator("a")).toHaveAttribute("href", /mapa/);
  });
});
