import { expect, type Locator, type Page } from "@playwright/test";

/**
 * Page Object панели администратора.
 *
 * Строка пользователя ищется по ячейке с его логином, а действия — уже внутри
 * этой строки. Так локатор не зависит ни от порядка строк, ни от того, что
 * ссылка «Роли» есть ещё и в шапке сайта.
 */
export class PanelPage {
  constructor(readonly page: Page) {}

  /**
   * Список постраничный (10 строк), поэтому нужного пользователя ищем через
   * `?q=`, а не рассчитываем, что он окажется на первой странице.
   */
  async goto(query?: string): Promise<void> {
    const url = query ? `/manage/?q=${encodeURIComponent(query)}` : "/manage/";
    await this.page.goto(url);
    await expect(this.heading).toBeVisible();
  }

  get searchBox(): Locator {
    return this.page.getByRole("searchbox");
  }

  /** То же самое, но руками через форму поиска — так проверяется и она. */
  async search(query: string): Promise<void> {
    await this.searchBox.fill(query);
    await this.page.getByRole("button", { name: "Найти" }).click();
    await expect(this.heading).toBeVisible();
  }

  get heading(): Locator {
    return this.page.getByRole("heading", { name: "Пользователи" });
  }

  get status(): Locator {
    return this.page.getByRole("status");
  }

  /** Строка таблицы, в которой логин совпадает целиком. */
  row(username: string): Locator {
    return this.page
      .getByRole("row")
      .filter({ has: this.page.getByRole("cell", { name: username, exact: true }) });
  }

  /** Бейдж роли внутри строки пользователя. */
  roleBadge(username: string, role: string): Locator {
    return this.row(username).getByText(role, { exact: true });
  }

  /**
   * Активность читаем по кнопке, а не по колонке: у активного пользователя
   * предлагают «Деактивировать», у отключённого — «Активировать».
   */
  toggleButton(username: string): Locator {
    return this.row(username).getByRole("button");
  }

  async isActive(username: string): Promise<boolean> {
    return (await this.toggleButton(username).innerText()) === "Деактивировать";
  }

  async toggleActive(username: string): Promise<void> {
    await this.toggleButton(username).click();
  }

  // --- форма ролей ---------------------------------------------------------

  async openRoles(username: string): Promise<void> {
    // Сначала сужаем список до нужного пользователя: ссылка «Роли» есть в
    // каждой строке, и на другой странице списка её просто не окажется.
    await this.goto(username);
    await this.row(username).getByRole("link", { name: "Роли" }).click();
    await expect(
      this.page.getByRole("heading", { name: `Роли пользователя ${username}` }),
    ).toBeVisible();
  }

  roleCheckbox(role: string): Locator {
    return this.page.getByRole("checkbox", { name: role, exact: true });
  }

  async saveRoles(): Promise<void> {
    await this.page.getByRole("button", { name: "Сохранить" }).click();
  }

  async cancelRoles(): Promise<void> {
    await this.page.getByRole("link", { name: "Отмена" }).click();
  }

  /** Привести набор ролей пользователя к нужному и сохранить. */
  async setRoles(username: string, roles: string[]): Promise<void> {
    await this.openRoles(username);

    for (const role of ["admin", "user"]) {
      const checkbox = this.roleCheckbox(role);
      if (roles.includes(role)) {
        await checkbox.check();
      } else {
        await checkbox.uncheck();
      }
    }

    await this.saveRoles();
  }

  // --- «Роли» и «Аудит» ----------------------------------------------------

  async gotoRoles(): Promise<void> {
    await this.page.goto("/manage/roles/");
    await expect(
      this.page.getByRole("heading", { name: "Роли", exact: true }),
    ).toBeVisible();
  }

  /** Ячейка со счётчиком участников роли — вторая колонка таблицы «Роли». */
  roleMembersCell(role: string): Locator {
    return this.page
      .getByRole("row")
      .filter({ has: this.page.getByRole("cell", { name: role, exact: true }) })
      .getByRole("cell")
      .last();
  }

  async roleMembers(role: string): Promise<number> {
    return Number(await this.roleMembersCell(role).innerText());
  }

  async gotoAudit(): Promise<void> {
    await this.page.goto("/manage/audit/");
    await expect(
      this.page.getByRole("heading", { name: "Аудит: изменения ролей" }),
    ).toBeVisible();
  }

  /**
   * Самая свежая запись журнала. У модели `ordering = ["-created_at", "-id"]`,
   * поэтому это первая строка тела таблицы.
   */
  get lastAuditRow(): Locator {
    return this.page.getByRole("rowgroup").last().getByRole("row").first();
  }

  // --- создание пользователя ----------------------------------------------

  async openCreateUser(): Promise<void> {
    await this.page.getByRole("link", { name: "+ Новый пользователь" }).click();
    await expect(
      this.page.getByRole("heading", { name: "Новый пользователь" }),
    ).toBeVisible();
  }

  async fillNewUser(data: {
    username: string;
    password: string;
    email?: string;
    roles?: string[];
  }): Promise<void> {
    await this.page.getByLabel("Имя пользователя").fill(data.username);
    if (data.email) {
      await this.page.getByLabel("Адрес электронной почты").fill(data.email);
    }
    for (const role of data.roles ?? []) {
      await this.roleCheckbox(role).check();
    }
    await this.page.getByLabel("Пароль:", { exact: true }).fill(data.password);
    await this.page.getByLabel("Подтверждение пароля").fill(data.password);
  }

  async submitNewUser(): Promise<void> {
    await this.page.getByRole("button", { name: "Создать" }).click();
  }
}
