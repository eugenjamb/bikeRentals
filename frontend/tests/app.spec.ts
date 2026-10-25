import { test, expect } from "@playwright/test";

test("case study, recorded results and a real forecast request", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/bike-rentals/");
  await expect(
    page.getByRole("heading", { name: /The city moves.*Stay ahead/ }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("navigation", { name: "Case study chapters" })
      .getByRole("link"),
  ).toHaveCount(8);
  const photos = page.locator(".ride-hero-image, .street-photo img");
  await expect(photos).toHaveCount(3);
  for (const photo of await photos.all()) {
    await photo.scrollIntoViewIfNeeded();
    await expect
      .poll(() =>
        photo.evaluate((image) => (image as HTMLImageElement).naturalWidth),
      )
      .toBeGreaterThan(0);
  }
  const resultFigure = page.locator(".result-figure");
  await resultFigure.scrollIntoViewIfNeeded();
  await expect
    .poll(() =>
      resultFigure.evaluate(
        (image) => (image as HTMLImageElement).naturalWidth,
      ),
    )
    .toBeGreaterThan(0);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.screenshot({
    path: "test-results/case-study-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: /Forecast lab/ })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "One hour. A real prediction." }),
  ).toBeVisible();
  const predictionRequest = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/predict") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Predict next-hour demand" }).click();
  expect((await predictionRequest).status()).toBe(200);
  await expect(page.getByText(/Pipeline completed in/)).toBeVisible();
  await expect(page.getByText("Actually observed")).toBeVisible();
  await page.screenshot({
    path: "test-results/forecast-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: /Weekend afternoon/ }).click();
  await page.getByRole("button", { name: "Predict next-hour demand" }).click();
  await expect(page.getByText(/Pipeline completed in/)).toBeVisible();
  expect(errors).toEqual([]);
});

test("mobile layout and an invalid custom payload", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/bike-rentals/");
  await expect(
    page.getByRole("heading", { name: /The city moves.*Stay ahead/ }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "test-results/case-study-mobile.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: /Forecast lab/ })
    .first()
    .click();
  await page.getByText("Developer mode: custom request").click();
  await page.getByRole("checkbox").check();
  await page
    .getByRole("textbox", { name: "Custom prediction request JSON" })
    .fill("{}");
  await page.getByRole("button", { name: "Predict next-hour demand" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await page.screenshot({
    path: "test-results/forecast-mobile.png",
    fullPage: true,
  });
});
