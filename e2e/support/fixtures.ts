import { test as base, expect, type Page } from "@playwright/test";

import { FileManagerPage } from "./file-manager.page";
import { PanelPage } from "./panel.page";

/** Учётка берётся из окружения: в CI это demo-пользователь из seed_demo_users. */
export const credentials = {
  username: process.env.E2E_USERNAME ?? "demo_admin",
  password: process.env.E2E_PASSWORD ?? "demo-password-123",
};

/** Уникальное имя на каждый прогон: тесты не мешают друг другу и повторяемы. */
export function uniqueName(prefix: string): string {
  const stamp = Date.now().toString(36);
  const random = Math.random().toString(36).slice(2, 7);
  return `${prefix}-${stamp}-${random}`;
}

export async function login(page: Page): Promise<void> {
  await page.goto("/login/");
  await page.getByLabel("Имя пользователя").fill(credentials.username);
  await page.getByLabel("Пароль").fill(credentials.password);
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page.getByRole("heading", { name: /Вы вошли как/ })).toBeVisible();
}

type Fixtures = {
  /** Файловый менеджер под залогиненным пользователем. */
  fileManager: FileManagerPage;
  /** Панель администратора под залогиненным админом. */
  panel: PanelPage;
  /** Пустая папка под конкретный тест, которая убирается за собой. */
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
    const folder = uniqueName(testInfo.title.replace(/[^a-zA-Zа-яА-Я0-9]+/g, "-"));

    await fileManager.goto();
    await fileManager.createFolder(folder);
    await fileManager.openFolder(folder);

    await use(folder);

    await fileManager.removeIfExists(folder);
  },
});

export { expect };
