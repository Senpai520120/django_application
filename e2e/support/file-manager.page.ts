import { expect, type Locator, type Page } from "@playwright/test";

/**
 * Page Object файлового менеджера.
 *
 * Все локаторы — по роли, лейблу или aria-label: они переживают правку вёрстки,
 * в отличие от CSS-селекторов, которые выдаёт codegen.
 */
export class FileManagerPage {
  constructor(readonly page: Page) {}

  async goto(path = ""): Promise<void> {
    const url = path ? `/files/?path=${encodeURIComponent(path)}` : "/files/";
    await this.page.goto(url);
    await expect(this.heading).toBeVisible();
  }

  get heading(): Locator {
    return this.page.getByRole("heading", { name: "Файлы" });
  }

  get status(): Locator {
    return this.page.getByRole("status");
  }

  /** Строка таблицы, в которой лежит запись с таким именем. */
  row(name: string): Locator {
    return this.page
      .getByRole("row")
      .filter({ has: this.page.getByRole("link", { name, exact: true }) });
  }

  entryLink(name: string): Locator {
    return this.page.getByRole("link", { name, exact: true });
  }

  async createFolder(name: string): Promise<void> {
    await this.page.getByLabel("Новая папка").fill(name);
    await this.page.getByRole("button", { name: "Создать папку" }).click();
  }

  async openFolder(name: string): Promise<void> {
    await this.entryLink(name).click();
    await expect(this.breadcrumbCurrent).toHaveText(name);
  }

  get breadcrumbCurrent(): Locator {
    return this.page.locator("[aria-current='page']");
  }

  async goToRootCrumb(): Promise<void> {
    await this.page.getByRole("link", { name: "Корень", exact: true }).click();
  }

  async goUp(): Promise<void> {
    await this.page.getByRole("link", { name: "← Наверх" }).click();
  }

  /** Загрузка файлов, собранных прямо в памяти теста. */
  async uploadFiles(
    files: { name: string; mimeType: string; buffer: Buffer }[],
  ): Promise<void> {
    await this.page.getByLabel("Загрузить файлы").setInputFiles(files);
    await this.page.getByRole("button", { name: "Загрузить", exact: true }).click();
  }

  async renameEntry(name: string, newName: string): Promise<void> {
    await this.page.getByRole("link", { name: `Переименовать ${name}` }).click();
    await this.page.getByLabel("Новое имя").fill(newName);
    await this.page.getByRole("button", { name: "Сохранить" }).click();
  }

  async deleteEntry(name: string, confirm = true): Promise<void> {
    await this.page.getByRole("link", { name: `Удалить ${name}` }).click();
    if (confirm) {
      await this.page.getByRole("button", { name: "Удалить" }).click();
    } else {
      await this.page.getByRole("link", { name: "Отмена" }).click();
    }
  }

  /** Удаление в уборке после теста: не падаем, если запись уже исчезла. */
  async removeIfExists(name: string): Promise<void> {
    await this.goto();
    if ((await this.entryLink(name).count()) > 0) {
      await this.deleteEntry(name);
    }
  }
}
