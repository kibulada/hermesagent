import { test } from '@playwright/test';
import { loginAsTimMedinesia } from '../utils/loginUtils';

test('capture prescription flow UI', async ({ page }) => {
  await loginAsTimMedinesia(page);
  await page.goto('https://development.kesia.id/outpatient', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  const firstRow = page.locator('td.ant-table-cell').first();
  if (await firstRow.count()) {
    await firstRow.click();
    await page.waitForTimeout(3000);
  }

  const finalUrl = page.url();
  console.log(`finalUrl=${finalUrl}`);

  // capture full page + all interactive text
  await page.screenshot({ path: 'screenshots/pp7439_patient_detail.png', fullPage: true });

  const buttons = await page.locator('button, a').allTextContents();
  const uniq = Array.from(new Set(buttons.map((b) => b.trim()).filter((b) => b.length > 0 && b.length < 40)));
  console.log(`buttons/links (unique, non-empty):`);
  for (const b of uniq) console.log(`  - ${b}`);
});