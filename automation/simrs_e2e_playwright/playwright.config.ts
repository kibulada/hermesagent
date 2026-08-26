import { defineConfig, devices } from '@playwright/test';
import * as dotenv from 'dotenv';
import * as path from 'path';

dotenv.config({ path: path.resolve(__dirname, '.env.staging') });

const baseURL = process.env.STAGING_BASE_URL;
if (!baseURL) {
  throw new Error('STAGING_BASE_URL missing in .env.staging');
}

export default defineConfig({
  testDir: '.',
  testIgnore: ['**/node_modules/**'],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  // JSON reporter wajib: runner.py membaca AC mana yang gagal dari sini.
  // Tanpa ini hasil cuma exit code -> "ada yang gagal" tanpa tahu apa.
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});