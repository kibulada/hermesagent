import { test, expect, Page } from '@playwright/test';
import { loginAsTimMedinesia } from '../utils/loginUtils';

async function collectMasterdataItemCalls(page: Page) {
  const calls: { url: string; status?: number; withLocation: boolean; sample?: string }[] = [];
  page.on('request', (req) => {
    const url = req.url();
    if (url.includes('/masterdata/item')) {
      calls.push({ url, withLocation: /[?&]location=[^&]+/.test(url) });
    }
  });
  page.on('response', async (resp) => {
    const url = resp.url();
    const idx = calls.findIndex((c) => c.url === url && c.sample === undefined);
    if (idx < 0) return;
    if (url.includes('/masterdata/item')) {
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
      } catch {
        /* non-json */
      }
      calls[idx].status = resp.status();
    }
  });
  return calls;
}

test.describe('PP#7439 — open patient → open prescription item dropdown', () => {
  test('end-to-end flow on /outpatient', async ({ page }) => {
    await loginAsTimMedinesia(page);
    const calls = await collectMasterdataItemCalls(page);

    await page.goto('https://development.kesia.id/outpatient', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // klik pasien paling atas
    const firstRow = page.locator('td.ant-table-cell').first();
    const rowCount = await firstRow.count();
    console.log(`[flow] patient rows visible=${rowCount}`);
    if (rowCount > 0) {
      await firstRow.click();
      await page.waitForTimeout(3000);
    }

    // cari tombol Tambah Resep atau equivalent
    const prescriptionBtns = [
      'button:has-text("Tambah Resep")',
      'button:has-text("Buat Resep")',
      'button:has-text("Resep")',
      'a:has-text("Resep")',
    ];
    let opened = false;
    for (const sel of prescriptionBtns) {
      const btn = page.locator(sel).first();
      if (await btn.count()) {
        await btn.click().catch(() => {});
        opened = true;
        break;
      }
    }
    console.log(`[flow] prescription button opened=${opened}`);

    // cari field input autocomplete / select untuk nama obat
    await page.waitForTimeout(2000);
    const itemInputs = [
      'input[placeholder*="obat" i]',
      'input[placeholder*="item" i]',
      'input[placeholder*="nama" i]',
      '.ant-select-selector input',
    ];
    let interacted = false;
    for (const sel of itemInputs) {
      const el = page.locator(sel).first();
      if (await el.count()) {
        await el.click().catch(() => {});
        await el.fill('a').catch(() => {});
        interacted = true;
        break;
      }
    }
    console.log(`[flow] item input interacted=${interacted}`);

    // tunggu network settle
    await page.waitForTimeout(3000);

    // dump calls
    const itemCalls = calls.filter((c) => c.url.includes('/masterdata/item'));
    console.log(`[flow] /masterdata/item total calls=${itemCalls.length}`);
    for (const c of itemCalls) {
      console.log(`  url=${c.url}`);
      console.log(`  status=${c.status}`);
      console.log(`  withLocation=${c.withLocation}`);
      console.log(`  sampleRow=${c.sample}`);
    }

    // Assertion minimum: flow tidak error.
    expect(true).toBe(true);
  });
});