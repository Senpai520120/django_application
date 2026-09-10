import { expect, test, uniqueName } from "./support/fixtures";

/**
 * Панель администратора в браузере.
 *
 * Роли и активность проверяются на демо-пользователе `demo_user`, поэтому
 * каждый тест возвращает его в исходное состояние — набор ролей `["user"]`
 * и активный аккаунт. Прогоны идут в один поток, так что состояние не гонится.
 */
const TARGET = "demo_user";

test.describe("Панель: роли", () => {
  test.afterEach(async ({ panel }) => {
    await panel.setRoles(TARGET, ["user"]);
  });

  test("админ назначает роль и она появляется в списке", async ({ panel }) => {
    await test.step("исходно у пользователя только роль user", async () => {
      await panel.goto(TARGET);
      await expect(panel.roleBadge(TARGET, "user")).toBeVisible();
      await expect(panel.roleBadge(TARGET, "admin")).toHaveCount(0);
    });

    await test.step("отмечаем роль admin и сохраняем", async () => {
      await panel.openRoles(TARGET);
      await panel.roleCheckbox("admin").check();
      await panel.saveRoles();
    });

    await test.step("роль видна в строке пользователя", async () => {
      await expect(panel.status).toContainText("обновлены");
      await expect(panel.roleBadge(TARGET, "admin")).toBeVisible();
      await expect(panel.roleBadge(TARGET, "user")).toBeVisible();
    });
  });

  test("админ снимает роль и она исчезает из списка", async ({ panel }) => {
    await test.step("снимаем единственную роль", async () => {
      await panel.openRoles(TARGET);
      await panel.roleCheckbox("user").uncheck();
      await panel.saveRoles();
    });

    await test.step("бейджа роли больше нет", async () => {
      await expect(panel.status).toContainText("обновлены");
      await expect(panel.roleBadge(TARGET, "user")).toHaveCount(0);
    });
  });

  test("отмена на форме ролей ничего не меняет", async ({ panel }) => {
    await panel.openRoles(TARGET);

    await test.step("отмечаем admin, но уходим по «Отмена»", async () => {
      await panel.roleCheckbox("admin").check();
      await panel.cancelRoles();
    });

    await test.step("роли остались прежними", async () => {
      await expect(panel.heading).toBeVisible();
      await panel.goto(TARGET);
      await expect(panel.roleBadge(TARGET, "admin")).toHaveCount(0);
      await expect(panel.roleBadge(TARGET, "user")).toBeVisible();
    });
  });

  test("админ не может снять роль admin с самого себя", async ({ panel }) => {
    await panel.openRoles("demo_admin");

    await test.step("пробуем убрать у себя единственную админскую роль", async () => {
      await panel.roleCheckbox("admin").uncheck();
      await panel.saveRoles();
    });

    await test.step("форма отказывает и объясняет причину", async () => {
      await expect(
        panel.page.getByText("Нельзя снять с себя роль admin"),
      ).toBeVisible();
    });

    await panel.cancelRoles();
    await panel.goto("demo_admin");
    await expect(panel.roleBadge("demo_admin", "admin")).toBeVisible();
  });
});

test.describe("Панель: активность", () => {
  // В CI у тестов есть ретраи: если прогон упадёт между отключением и включением
  // обратно, пользователь должен вернуться в активное состояние сам.
  test.afterEach(async ({ panel }) => {
    await panel.goto(TARGET);
    if (!(await panel.isActive(TARGET))) {
      await panel.toggleActive(TARGET);
    }
  });

  test("деактивация и обратная активация пользователя", async ({ panel }) => {
    await panel.goto(TARGET);
    expect(await panel.isActive(TARGET)).toBe(true);

    await test.step("отключаем пользователя", async () => {
      await panel.toggleActive(TARGET);

      await expect(panel.status).toContainText("деактивирован");
      await expect(panel.toggleButton(TARGET)).toHaveText("Активировать");
    });

    await test.step("включаем обратно", async () => {
      await panel.toggleActive(TARGET);

      await expect(panel.status).toContainText("активирован");
      await expect(panel.toggleButton(TARGET)).toHaveText("Деактивировать");
    });
  });
});

test.describe("Панель: аудит и счётчики", () => {
  test.afterEach(async ({ panel }) => {
    await panel.setRoles(TARGET, ["user"]);
  });

  test("выдача и снятие роли попадают в журнал аудита", async ({ panel }) => {
    await panel.setRoles(TARGET, ["admin", "user"]);

    await test.step("верхняя запись журнала: кто, что сделал, с какой ролью и кому", async () => {
      await panel.gotoAudit();
      const row = panel.lastAuditRow;

      await expect(
        row.getByRole("cell", { name: "demo_admin", exact: true }),
      ).toBeVisible();
      await expect(
        row.getByRole("cell", { name: "назначена", exact: true }),
      ).toBeVisible();
      await expect(row.getByRole("cell", { name: "admin", exact: true })).toBeVisible();
      await expect(row.getByRole("cell", { name: TARGET, exact: true })).toBeVisible();
    });

    await test.step("снятие роли пишется отдельной записью", async () => {
      await panel.setRoles(TARGET, ["user"]);
      await panel.gotoAudit();
      const row = panel.lastAuditRow;

      await expect(row.getByRole("cell", { name: "снята", exact: true })).toBeVisible();
      await expect(row.getByRole("cell", { name: "admin", exact: true })).toBeVisible();
      await expect(row.getByRole("cell", { name: TARGET, exact: true })).toBeVisible();
    });
  });

  test("счётчик на странице «Роли» идёт за выдачей роли", async ({ panel }) => {
    await panel.gotoRoles();
    const before = await panel.roleMembers("admin");

    await test.step("после выдачи в роли admin на одного больше", async () => {
      await panel.setRoles(TARGET, ["admin", "user"]);
      await panel.gotoRoles();
      await expect(panel.roleMembersCell("admin")).toHaveText(String(before + 1));
    });

    await test.step("после снятия счётчик возвращается", async () => {
      await panel.setRoles(TARGET, ["user"]);
      await panel.gotoRoles();
      await expect(panel.roleMembersCell("admin")).toHaveText(String(before));
    });
  });
});

test.describe("Панель: создание пользователя", () => {
  test("админ заводит пользователя и сразу выдаёт роль", async ({ panel }) => {
    // Удалять пользователей панель не умеет намеренно, поэтому уникальное имя —
    // единственный способ сделать тест повторяемым.
    const username = uniqueName("e2e").replace(/-/g, "_");

    await panel.openCreateUser();
    await panel.fillNewUser({
      username,
      password: "E2e-Strong-Pass-42",
      email: `${username}@example.com`,
      roles: ["user"],
    });
    await panel.submitNewUser();

    await test.step("пользователь появился в списке с выданной ролью", async () => {
      await expect(panel.status).toContainText("создан");
      await panel.search(username);
      await expect(panel.row(username)).toBeVisible();
      await expect(panel.roleBadge(username, "user")).toBeVisible();
    });
  });

  test("слишком простой пароль не принимается", async ({ panel }) => {
    const username = uniqueName("weak").replace(/-/g, "_");

    await panel.openCreateUser();
    await panel.fillNewUser({ username, password: "52012000" });
    await panel.submitNewUser();

    await test.step("форма объясняет, что не так, и пользователя не создаёт", async () => {
      await expect(
        panel.page.getByText("Введённый пароль состоит только из цифр"),
      ).toBeVisible();

      // После отказа мы всё ещё на форме, поэтому за списком идём по адресу.
      await panel.goto(username);
      await expect(panel.page.getByText("Ничего не найдено")).toBeVisible();
      await expect(panel.row(username)).toHaveCount(0);
    });
  });
});
