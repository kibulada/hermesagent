import { test } from '@playwright/test';
import { loginAsTimMedinesia } from '../utils/loginUtils';

const PATHS = [
  '/outpatient/registration',
  '/outpatientDoctor',
  '/erDoctor',
  '/inpatient/registration',
  '/inpatientDoctor',
  '/pharmacy',
];

test('probe all likely prescription entry points', async ({ page }) => {
  await loginAsTimMedinesia(page);

  for (const path of PATHS) {
    const resp = await page.goto(`https://development.kesia.id${path}`, { waitUntil: 'domcontentloaded' }).catch(() => null);
    const status = resp?.status();
    const finalUrl = page.url();
    const has404 = finalUrl.includes('/404');
    console.log(`path=${path} httpStatus=${status} finalUrl=${finalUrl} has404=${has404}`);
    await page.waitForTimeout(1000);
  }
});