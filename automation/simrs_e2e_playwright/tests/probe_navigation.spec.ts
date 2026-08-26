import { test, expect } from '@playwright/test';
import { loginAsTimMedinesia } from '../utils/loginUtils';

/**
 * PP#7307 + PP#7439 — Coba navigasi langsung ke modul rawat jalan / IGD
 * agar dropdown prescription terbuka dan trigger /masterdata/item?location=...
 */

const CANDIDATE_PATHS = [
  '/doctorDashboard',
  '/outpatient',
  '/outpatientDoctor',
  '/erDoctor',
  '/inpatientDoctor',
];

test.describe('PP#7439 — Direct navigation probes', () => {
  for (const path of CANDIDATE_PATHS) {
    test(`probe ${path}`, async ({ page }) => {
      await loginAsTimMedinesia(page);

      const calls: string[] = [];
      page.on('request', (req) => {
        const url = req.url();
        if (url.includes('/masterdata/item')) calls.push(url);
      });

      const resp = await page.goto(`https://development.kesia.id${path}`, { waitUntil: 'networkidle' }).catch((e) => null);
      const finalUrl = page.url();
      await page.waitForTimeout(2500);

      console.log(`[probe ${path}] httpStatus=${resp?.status?.() ?? 'n/a'} finalUrl=${finalUrl}`);
      console.log(`[probe ${path}] masterdata/item calls=${calls.length}`);
      for (const u of calls) console.log(`  ${u}`);
    });
  }
});