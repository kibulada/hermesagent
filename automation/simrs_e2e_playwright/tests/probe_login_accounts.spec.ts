import { test, expect, Page } from '@playwright/test';

async function tryLogin(page: Page, user: string, pass: string, orgLabel: string) {
  await page.goto('/signin');
  await page.fill('#login_username', user);
  await page.fill('#login_password', pass);
  // open dropdown org
  await page.locator('.ant-select-selector').first().click();
  await page.waitForTimeout(500);
  const opt = page.locator(`div[title*="${orgLabel}" i]`).first();
  const has = await opt.count();
  if (!has) {
    console.log(`  user=${user} org=${orgLabel} not found`);
    return null;
  }
  await opt.click();
  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);
  const url = page.url();
  console.log(`  user=${user} -> ${url}`);
  return url;
}

const CREDENTIALS: Array<[string, string, string]> = process.env.PROBE_CREDENTIALS
  ? JSON.parse(process.env.PROBE_CREDENTIALS)
  : [];

test('probe login for doctor-capable accounts', async ({ page }) => {
  if (CREDENTIALS.length === 0) {
    test.skip(true, 'PROBE_CREDENTIALS not set; skip probe.');
  }
  for (const [u, p, o] of CREDENTIALS) {
    await tryLogin(page, u, p, o);
  }
  expect(true).toBe(true);
});