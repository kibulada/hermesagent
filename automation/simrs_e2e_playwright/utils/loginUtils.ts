import { Page, expect } from '@playwright/test';

function requireEnv(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`${name} missing in .env.staging`);
  return v;
}

export async function loginAsTimMedinesia(page: Page) {
  const username = requireEnv('STAGING_TEST_USERNAME');
  const password = requireEnv('STAGING_TEST_PASSWORD');
  const tenant = requireEnv('STAGING_TEST_TENANT');

  await page.goto('/signin');
  await page.fill('#login_username', username);
  await page.fill('#login_password', password);
  await page.locator('.ant-select-selector').first().click();
  await page.locator(`div[title="${tenant}"]`).click();
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/.*doctorDashboard/);
}
