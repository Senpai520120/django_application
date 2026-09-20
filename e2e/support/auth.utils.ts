import { expect, type Locator, type Page } from "@playwright/test";

/**
 * Login utils
 *
 */
export class LoginUtils {
  constructor(readonly page: Page) {}

  async login(username: string, password: string): Promise<void> {
    await this.page.goto('http://127.0.0.1:8000/login/?next=/');
    await expect(this.page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
    await this.page.getByRole('textbox', { name: 'Username' }).click();
    await this.page.getByRole('textbox', { name: 'Username' }).fill(username);
    await this.page.getByRole('textbox', { name: 'Password' }).click();
    await this.page.getByRole('textbox', { name: 'Password' }).fill(password);
    await this.page.getByRole('button', { name: 'Sign in' }).click();
    await expect(this.page.getByRole('heading', { name: 'You are signed in as' })).toBeVisible();
  }
  
}


