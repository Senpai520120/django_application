import { test as base, expect, type Page } from "@playwright/test";

import { FileManagerPage } from "./file-manager.page";
import { PanelPage } from "./panel.page";

/** Credentials come from the environment; in CI it is a seed_demo_users account. */
export const credentials = {
  username: process.env.E2E_USERNAME ?? "demo_admin",
  password: process.env.E2E_PASSWORD ?? "demo-password-123",
};

/** A unique name per run, so tests never collide and stay repeatable. */
export function uniqueName(prefix: string): string {
  const stamp = Date.now().toString(36);
  const random = Math.random().toString(36).slice(2, 7);
  return `${prefix}-${stamp}-${random}`;
}

export async function login(page: Page): Promise<void> {
  await page.goto("/login/");
  await page.getByLabel("Username").fill(credentials.username);
  await page.getByLabel("Password").fill(credentials.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: /You are signed in as/ })).toBeVisible();
}

type Fixtures = {
  /** File manager under a signed-in user. */
  fileManager: FileManagerPage;
  /** Admin panel under a signed-in admin. */
  panel: PanelPage;
  /** An empty folder for one test that cleans up after itself. */
  workspace: string;
};

export const test = base.extend<Fixtures>({
  fileManager: async ({ page }, use) => {
    await login(page);
    const fileManager = new FileManagerPage(page);
    await fileManager.goto();
    await use(fileManager);
  },

  panel: async ({ page }, use) => {
    await login(page);
    const panel = new PanelPage(page);
    await panel.goto();
    await use(panel);
  },

  workspace: async ({ fileManager }, use, testInfo) => {
    const folder = uniqueName(testInfo.title.replace(/[^a-zA-Z0-9]+/g, "-"));

    await fileManager.goto();
    await fileManager.createFolder(folder);
    await fileManager.openFolder(folder);

    await use(folder);

    await fileManager.removeIfExists(folder);
  },
});

export { expect };
