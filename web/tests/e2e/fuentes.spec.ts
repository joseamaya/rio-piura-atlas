import { expect, test } from "@playwright/test";

test.describe("catálogo de fuentes y registros documentales", () => {
  test("filtra por disponibilidad y busca una fuente", async ({ page }) => {
    await page.goto("fuentes/");
    await expect(page.locator(".record")).toHaveCount(49);

    await page.selectOption("#availabilityFilter", "documental");
    await expect(page.locator("#filterCount")).toContainText("de 49 fuentes visibles");
    await expect(page.locator("#pechp-inspeccion-2026")).toBeVisible();
    await expect(page.locator("#ana-subcuencas")).toBeHidden();

    await page.selectOption("#availabilityFilter", "all");
    await page.fill("#searchFilter", "PISCO");
    await expect(page.locator("#senamhi-pisco")).toBeVisible();
    await expect(page.locator("#filterCount")).not.toContainText("40 de 40");
  });

  test("muestra los registros de la cuenca baja sin geometría nueva", async ({ page }) => {
    await page.goto("escenarios/");
    const section = page.locator("#registros-cuenca-baja");
    await expect(section).toBeVisible();
    await expect(section.locator(".lowbasin-record")).toHaveCount(3);
    await expect(section).toContainText("San Pedro, Virrilá y Reventazón");
    await expect(section).toContainText("Virrilá deposita; Sechura transporta más");
    await expect(section).toContainText("Tapa de Cuy, La Niña y Chutuque");
    await expect(
      section.locator('a[href*="#pechp-inspeccion-2026"]'),
    ).toBeVisible();
    await expect(
      section.locator('a[href*="#peruverde-expedicion-2002"]').first(),
    ).toBeVisible();
  });
});
