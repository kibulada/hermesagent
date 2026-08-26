import { test, expect } from '@playwright/test';
import { loginAsTimMedinesia } from '../utils/loginUtils';

test('Navigate to PPI menu', async ({ page }) => {
  await loginAsTimMedinesia(page);

  // 1. Klik di pojok kanan untuk munculin semua menu
  // Menggunakan class gabungan sebagai selector. Playwright akan memilih yang pertama jika ada beberapa.
  await page.locator('.sc-gFAWRd.jUaqBn.text-right').click();

  // 2. Pilih menu Perawat Rawat Inap
  await page.locator('text=Perawat Rawat Inap').click();

  // 3. Klik pasien paling atas dari list pasien
  // Asumsi list pasien langsung muncul setelah klik Perawat Rawat Inap.
  // Akan mencoba locator yang paling umum untuk item di list pasien dan mengklik yang pertama.
  // Kalau ada class spesifik untuk item pasien, itu lebih baik. Saya akan coba dengan tag div atau li.
  await page.locator('td.ant-table-cell').first().click(); // Asumsi pasien diwakili oleh cell pertama di tabel

  // 4. Klik Lainnya di sidemenu kiri
  await page.locator('a').filter({ hasText: 'Lainnya' }).click(); // Menggunakan selector yang lebih spesifik untuk menu sidemenu

  // 5. Klik menu PPI
  // Ini adalah step terakhir untuk sampai di https://development.kesia.id/inpatientNurse/ppi
  // Saya asumsikan ada elemen dengan teks "PPI" yang bisa diklik setelah "Lainnya" diklik
  await page.locator('text=PPI').click();

  // Verifikasi URL setelah navigasi
  await expect(page).toHaveURL('https://development.kesia.id/inpatientNurse/ppi');
});