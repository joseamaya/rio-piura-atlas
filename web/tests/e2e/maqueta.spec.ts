import { expect, test } from "@playwright/test";
import { openMaqueta } from "./helpers";

test.describe("maqueta 3D", () => {
  test("anuncia la carga y oculta el estado cuando el modelo está listo", async ({ page }) => {
    await page.route("**/models/piura.glb", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 400));
      await route.continue();
    });

    await page.goto("maqueta/");
    await expect(page.locator("#scene-status")).toBeVisible();
    await expect(page.locator("#scene-status")).toContainText("Cargando maqueta");
    await expect(page.locator("#maqueta-stage")).toHaveClass(/is-loaded/, { timeout: 20_000 });
    await expect(page.locator("#scene-status")).toBeHidden();
    await expect(page.locator("#scene")).toHaveAttribute("aria-busy", "false");
  });

  test("si el GLB falla, deja un estado de error y el enlace al mapa", async ({ page }) => {
    await page.route("**/models/piura.glb", (route) => route.abort());
    await page.goto("maqueta/");

    const status = page.locator("#scene-status");
    await expect(status).toBeVisible();
    await expect(status).toContainText("No se pudo cargar la maqueta");
    await expect(status.getByRole("link", { name: "Usa el mapa 2D" })).toHaveAttribute(
      "href",
      /mapa/,
    );
    await expect(page.locator("#scene")).toHaveAttribute("aria-busy", "false");
  });

  test("renderiza, responde a los controles y reinicia con teclado", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    await openMaqueta(page);

    await expect(page.locator("#scene canvas")).toBeVisible();
    await expect(page.locator("#scene")).toHaveAttribute("tabindex", "0");
    await expect(page.locator("#scene")).toHaveAttribute("aria-busy", "false");

    await page.locator("#scene").focus();
    await page.keyboard.press("Home");
    await page.keyboard.press("+");
    await page.keyboard.press("-");
    await expect(page.locator("#scene")).toBeFocused();

    await page.locator('[data-scene-action="zoom-in"]').click();
    await page.locator('[data-scene-action="reset"]').click();
    expect(errors).toEqual([]);
  });

  test("redimensiona el canvas al cambiar el tamaño del contenedor", async ({ page }) => {
    await openMaqueta(page);
    await page.setViewportSize({ width: 768, height: 1024 });

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
});
