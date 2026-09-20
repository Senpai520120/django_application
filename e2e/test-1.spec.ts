import { test, expect } from '@playwright/test';

test('test', async ({ page }) => {
  await page.goto('http://localhost:8000/login/?next=/');
  await page.getByRole('textbox', { name: 'Username' }).click();
  await page.getByRole('textbox', { name: 'Username' }).fill('e2e_mu5r0msu_jw8br');
  await page.getByRole('textbox', { name: 'Password' }).click();
});