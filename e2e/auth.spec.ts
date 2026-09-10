import { expect, test as anonymous } from "@playwright/test";

import { test } from "./support/fixtures";

anonymous.describe("Доступ к разделу", () => {
  anonymous("аноним отправляется на логин, а не видит файлы", async ({ page }) => {
    await page.goto("/files/");

    await expect(page).toHaveURL("/login/?next=/files/");
    await expect(page.getByRole("heading", { name: "Вход" })).toBeVisible();
  });

  anonymous("аноним не может открыть вложенную папку по прямой ссылке", async ({
    page,
  }) => {
    await page.goto("/files/?path=docs");

    await expect(page).toHaveURL(/\/login\//);
  });

  anonymous("неверные данные не пускают и не выдают, есть ли такой юзер", async ({
    page,
  }) => {
    await page.goto("/login/");

    await page.getByLabel("Имя пользователя").fill("demo_admin");
    await page.getByLabel("Пароль").fill("совсем-не-тот-пароль");
    await page.getByRole("button", { name: "Войти" }).click();

    const wrongPassword = await page.getByRole("listitem").first().innerText();

    await expect(page.getByRole("heading", { name: "Вход" })).toBeVisible();
    expect(wrongPassword).toContain("Пожалуйста, введите правильные");

    await page.getByLabel("Имя пользователя").fill("такого-юзера-нет");
    await page.getByLabel("Пароль").fill("совсем-не-тот-пароль");
    await page.getByRole("button", { name: "Войти" }).click();

    const unknownUser = await page.getByRole("listitem").first().innerText();

    // Тексты совпадают, значит по ответу нельзя понять, существует ли логин.
    expect(unknownUser).toBe(wrongPassword);
  });
});

test.describe("Вход и переход в раздел", () => {
  test("после логина в шапке есть ссылка на файлы", async ({ fileManager }) => {
    const { page } = fileManager;

    await test.step("возвращаемся на главную", async () => {
      await page.goto("/");
      await expect(page.getByRole("heading", { name: /Вы вошли как/ })).toBeVisible();
    });

    await test.step("переходим в файловый менеджер из шапки", async () => {
      await page.getByRole("link", { name: "Файлы", exact: true }).click();
      await expect(page.getByRole("heading", { name: "Файлы" })).toBeVisible();
      await expect(page).toHaveURL(/\/files\//);
    });
  });
});
