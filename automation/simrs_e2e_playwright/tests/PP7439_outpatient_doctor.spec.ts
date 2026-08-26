import { test, expect } from '@playwright/test';
import { loginAsTimMedinesia } from '../utils/loginUtils';

test('PP#7439 — explore /outpatientDoctor', async ({ page }) => {
  await loginAsTimMedinesia(page);

  const calls: { url: string; status?: number; withLocation: boolean; sample?: string }[] = [];
  page.on('request', (req) => {
    const url = req.url();
    if (url.includes('/masterdata/item')) {
      calls.push({ url, withLocation: /[?&]location=[^&]+/.test(url) });
    }
  });
  page.on('response', async (resp) => {
    const url = resp.url();
    if (!url.includes('/masterdata/item')) return;
    const idx = calls.findIndex((c) => c.url === url && c.sample === undefined);
    if (idx < 0) return;
    try {
      const body = await resp.text();
      const parsed = JSON.parse(body);
      const rows = parsed?.data?.rows ?? parsed?.rows ?? [];
      if (Array.isArray(rows) && rows.length > 0) {
        const f = rows[0];
        calls[idx].sample = JSON.stringify({
          id: f?.id,
          name: f?.name,
          stock: f?.stock ?? null,
          stockUpdatedAt: f?.stockUpdatedAt ?? null,
        });
      }
    } catch { /* non-json */ }
    calls[idx].status = resp.status();
  });

  await page.goto('https://development.kesia.id/outpatientDoctor', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  await page.screenshot({ path: 'screenshots/pp7439_outpatient_doctor.png', fullPage: true });

  const finalUrl = page.url();
  console.log(`finalUrl=${finalUrl}`);

  const buttons = await page.locator('button, a').allTextContents();
  const uniq = Array.from(new Set(buttons.map((b) => b.trim()).filter((b) => b.length > 0 && b.length < 40)));
  console.log(`buttons (unique):`);
  for (const b of uniq) console.log(`  - ${b}`);

  console.log(`masterdata/item calls=${calls.length}`);
  for (const c of calls) {
    console.log(`  url=${c.url}`);
    console.log(`  status=${c.status} withLocation=${c.withLocation} sample=${c.sample}`);
  }

  expect(true).toBe(true);
});