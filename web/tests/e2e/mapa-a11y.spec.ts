import { expect, test } from "@playwright/test";
import { openMap } from "./helpers";

test.describe("mapa · foco y teclado", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test("la ficha de la cuenca mueve el foco al encabezado y lo devuelve", async ({ page }) => {
    await openMap(page);
    const scrollBefore = await page.evaluate(() => window.scrollY);
    const trigger = page.locator("#ficha-cuenca");
    await trigger.focus();
    await trigger.press("Enter");

    await expect(page.locator("#ficha")).toHaveClass(/open/);
    expect(await page.evaluate(() => window.scrollY)).toBe(scrollBefore);
    await expect(page.locator("#ficha")).toHaveAttribute("aria-hidden", "false");
    await expect(page.locator("#ficha h3")).toBeFocused();

    await page.keyboard.press("Escape");
    await expect(page.locator("#ficha")).toHaveAttribute("aria-hidden", "true");
    await expect(page.locator("#ficha")).toHaveAttribute("inert", "");
    await expect(trigger).toBeFocused();
  });

  test("la ficha abierta desde el mapa devuelve el foco al lienzo", async ({ page }) => {
    await openMap(page);
    const box = await page.locator("#map").boundingBox();
    if (!box) throw new Error("sin caja del mapa");

    await page.locator("#map canvas").click({
      position: { x: Math.round(box.width * 0.5), y: Math.round(box.height * 0.5) },
    });
    await expect(page.locator("#ficha")).toHaveClass(/open/);
    await expect(page.locator("#ficha h3")).toBeFocused();

    await page.keyboard.press("Escape");
    await expect(page.locator("#ficha")).toHaveAttribute("aria-hidden", "true");
    await expect(page.locator("#map canvas")).toBeFocused();
  });

  test("el botón de cierre de la ficha devuelve el foco al disparador", async ({ page }) => {
    await openMap(page);
    await page.locator("#ficha-cuenca").click();
    await expect(page.locator("#ficha")).toHaveClass(/open/);

    await page.locator("#ficha-close").click();
    await expect(page.locator("#ficha")).toHaveAttribute("aria-hidden", "true");
    await expect(page.locator("#ficha-cuenca")).toBeFocused();
  });

  test("el mapa no se anuncia como aplicación y expone nombre e instrucciones", async ({ page }) => {
    await openMap(page);

    await expect(page.locator("#map")).not.toHaveAttribute("role", "application");
    const canvas = page.locator("#map canvas");
    await expect(canvas).toHaveAttribute("role", "region");
    await expect(canvas).toHaveAttribute("aria-label", "Mapa interactivo de la cuenca del río Piura");
    await expect(canvas).toHaveAttribute("aria-describedby", "map-summary map-instructions");
    await expect(canvas).toHaveAttribute("aria-busy", "false");
    await expect(page.locator("#map-status")).toContainText("Mapa interactivo listo");
    await expect(page.locator("#map-instructions")).toContainText("flechas");

    const zoomIn = page.locator('[data-action="zoom-in"]');
    await zoomIn.focus();
    await expect(zoomIn).toBeFocused();
    await expect(zoomIn).toHaveAttribute("aria-label", "Acercar");
    await page.keyboard.press("Enter");
  });

  test("el resumen textual enumera capas, cifras y fuentes", async ({ page }) => {
    await openMap(page);
    await page.locator("#map-alt summary").click();

    const alt = page.locator("#map-alt");
    await expect(alt).toHaveAttribute("open", "");
    await expect(alt).toContainText("10 938 km²");
    await expect(alt).toContainText("96,5 y 459,0 km²");
    await expect(alt).toContainText("Cómo recorrerlo");
    await expect(alt.getByRole("link", { name: "Copernicus EMSR199" })).toHaveAttribute(
      "href",
      /fuentes#copernicus-ems-emsr199/,
    );
  });

  test("el perfil de corte recibe el foco y lo devuelve al enlace", async ({ page }) => {
    await openMap(page);
    await page.locator(".cortes-list summary").click();
    const link = page.locator(".corte-link").first();
    await link.click();

    await expect(page.locator("#corte-panel")).toBeVisible();
    await expect(page.locator("#corte-title")).toBeFocused();

    await page.keyboard.press("Escape");
    await expect(page.locator("#corte-panel")).toBeHidden();
    await expect(link).toBeFocused();
  });

  test("el panel de escritorio no es modal ni inutiliza el mapa", async ({ page }) => {
    await openMap(page);
    const panel = page.locator(".map-panel");
    await expect(panel).toBeVisible();
    await expect(panel).not.toHaveAttribute("role", "dialog");
    await expect(panel).not.toHaveAttribute("aria-modal", "true");
    await expect(page.locator(".map-stage")).not.toHaveAttribute("inert", "");
    await expect(page.locator("#toggle-panel")).toBeHidden();
    await expect(page.locator("#map canvas")).toBeVisible();
  });

  test("si WebGL falla, el mapa muestra una alternativa en vez de un lienzo vacío", async ({ page }) => {
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

    await page.goto("mapa/");
    await expect(page.locator("#map-fallback")).toBeVisible();
    await expect(page.locator("#map-fallback")).toContainText("No se pudo iniciar el mapa interactivo");
    await expect(page.locator("#map")).toBeHidden();
    await expect(page.locator("#map-status")).toContainText("No se pudo iniciar el mapa interactivo");
    await expect(page.locator("#draw-corte")).toBeDisabled();
  });
});

test.describe("mapa · panel de capas móvil", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("abre como diálogo modal, atrapa el foco y vuelve al botón", async ({ page }) => {
    await openMap(page);
    const panel = page.locator(".map-panel");
    const toggle = page.locator("#toggle-panel");
    await expect(panel).toHaveClass(/collapsed/);
    await expect(toggle).toHaveAttribute("aria-expanded", "false");

    await toggle.click();
    await expect(panel).not.toHaveClass(/collapsed/);
    await expect(panel).toHaveAttribute("role", "dialog");
    await expect(panel).toHaveAttribute("aria-modal", "true");
    await expect(page.locator("#panel-title")).toBeFocused();
    await expect(page.locator(".map-stage")).toHaveAttribute("inert", "");
    await expect(page.locator(".site-header")).toHaveAttribute("inert", "");
    await expect(page.locator("body")).toHaveCSS("overflow", "hidden");

    const box = await panel.boundingBox();
    expect(box?.x ?? -1).toBeGreaterThanOrEqual(0);
    expect(box?.width ?? 999).toBeLessThanOrEqual(390);

    for (let i = 0; i < 28; i++) {
      await page.keyboard.press("Tab");
      const inside = await page.evaluate(
        () => document.querySelector(".map-panel")?.contains(document.activeElement) ?? false,
      );
      expect(inside).toBe(true);
    }

    await page.keyboard.press("Escape");
    await expect(panel).toHaveClass(/collapsed/);
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(toggle).toBeFocused();
    await expect(panel).not.toHaveAttribute("role", "dialog");
    await expect(page.locator(".map-stage")).not.toHaveAttribute("inert", "");
    await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
  });

  test("el botón de cierre devuelve el foco y no deja el fondo inerte", async ({ page }) => {
    await openMap(page);
    await page.locator("#toggle-panel").click();
    await expect(page.locator("#panel-close")).toBeVisible();

    await page.locator("#panel-close").click();
    await expect(page.locator(".map-panel")).toHaveClass(/collapsed/);
    await expect(page.locator("#toggle-panel")).toBeFocused();
    await expect(page.locator(".map-stage")).not.toHaveAttribute("inert", "");
  });

  test("la ficha de la cuenca se abre desde el panel sin dejar el fondo inerte", async ({ page }) => {
    await openMap(page);
    await page.locator("#toggle-panel").click();
    await page.locator("#ficha-cuenca").click();

    await expect(page.locator("#ficha")).toHaveClass(/open/);
    await expect(page.locator("#ficha h3")).toBeFocused();
    await expect(page.locator(".map-panel")).toHaveClass(/collapsed/);
    await expect(page.locator(".map-panel")).not.toHaveAttribute("role", "dialog");
    await expect(page.locator(".map-stage")).not.toHaveAttribute("inert", "");
  });

  test("la leyenda se cierra con Escape y no tapa los controles", async ({ page }) => {
    await openMap(page);
    const toggle = page.locator("#legend-toggle");
    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await expect(toggle).toHaveText("Cerrar leyenda");
    await expect(page.locator("#map-legend")).toBeVisible();

    const legend = await page.locator("#map-legend").boundingBox();
    const controls = await page.locator(".map-controls").boundingBox();
    expect(legend).not.toBeNull();
    expect(controls).not.toBeNull();
    if (legend && controls) {
      expect(legend.y).toBeGreaterThanOrEqual(controls.y + controls.height - 1);
    }

    await page.keyboard.press("Escape");
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await expect(toggle).toHaveText("Leyenda");
    await expect(toggle).toBeFocused();
  });
});
