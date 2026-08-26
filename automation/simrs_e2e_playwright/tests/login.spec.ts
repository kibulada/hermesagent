import { test, expect } from '@playwright/test';
import { loginAsTimMedinesia } from '../utils/loginUtils'; // Import the login utility

test('User can successfully login to SIMRS using login utility', async ({ page }) => {
  await loginAsTimMedinesia(page); // Use the utility function
});
