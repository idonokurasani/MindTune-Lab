import { test, expect } from '@playwright/test';

test.describe('Research console smoke', () => {
  test('loads the console and shows the navigation', async ({ page }) => {
    await page.goto('http://127.0.0.1:5173');
    await expect(page.locator('text=MindTune Research Console')).toBeVisible();
    await expect(page.locator('nav')).toBeVisible();
    await expect(page.locator('button:has-text("Overview")')).toBeVisible();
  });
});
