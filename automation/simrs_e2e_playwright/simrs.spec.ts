import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/signin');
  await expect(page).toHaveTitle(/Kesia/);
});

test('has login form', async ({ page }) => {
    await page.goto('/signin');
    await expect(page.locator('#login_username')).toBeVisible();
    await expect(page.locator('#login_password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
});