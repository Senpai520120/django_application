import { expect, test, uniqueName } from "./support/fixtures";

test.describe("Папки", () => {
  test("создание вложенной папки и возврат по хлебным крошкам", async ({
    fileManager,
    workspace,
  }) => {
    const nested = uniqueName("вложенная");

    await test.step("создаём папку внутри рабочей", async () => {
      await fileManager.createFolder(nested);
      await expect(fileManager.entryLink(nested)).toBeVisible();
    });

    await test.step("заходим внутрь", async () => {
      await fileManager.openFolder(nested);
      await expect(fileManager.page.getByText("Папка пуста")).toBeVisible();
    });

    await test.step("возвращаемся по крошке в родительскую папку", async () => {
      await fileManager.page.getByRole("link", { name: workspace, exact: true }).click();
      await expect(fileManager.breadcrumbCurrent).toHaveText(workspace);
      await expect(fileManager.entryLink(nested)).toBeVisible();
    });

    await test.step("возвращаемся в корень", async () => {
      await fileManager.goToRootCrumb();
      await expect(fileManager.entryLink(workspace)).toBeVisible();
    });
  });

  test("папка с уже занятым именем не создаётся дважды", async ({
    fileManager,
    workspace,
  }) => {
    const name = uniqueName("дубль");

    await fileManager.createFolder(name);
    await expect(fileManager.entryLink(name)).toBeVisible();

    await test.step("повторное создание показывает понятную ошибку", async () => {
      await fileManager.createFolder(name);

      await expect(fileManager.status).toContainText("уже существует");
      await expect(fileManager.entryLink(name)).toHaveCount(1);
    });

    await fileManager.goto(workspace);
  });

  test("удаление папки требует подтверждения", async ({ fileManager, workspace }) => {
    const name = uniqueName("на-удаление");
    await fileManager.createFolder(name);

    await test.step("отмена оставляет папку на месте", async () => {
      await fileManager.deleteEntry(name, false);
      await expect(fileManager.entryLink(name)).toBeVisible();
    });

    await test.step("подтверждение удаляет её", async () => {
      await fileManager.deleteEntry(name);
      await expect(fileManager.status).toContainText("Удалено");
      await expect(fileManager.entryLink(name)).toHaveCount(0);
    });

    await fileManager.goto(workspace);
  });

  test("удаление папки уносит вложенное содержимое", async ({
    fileManager,
    workspace,
  }) => {
    const folder = uniqueName("с-содержимым");

    await fileManager.createFolder(folder);
    await fileManager.openFolder(folder);
    await fileManager.uploadFiles([
      {
        name: "inside.txt",
        mimeType: "text/plain",
        buffer: Buffer.from("внутри папки"),
      },
    ]);
    await expect(fileManager.entryLink("inside.txt")).toBeVisible();

    await test.step("страница подтверждения предупреждает про содержимое", async () => {
      await fileManager.goto(workspace);
      await fileManager.page.getByRole("link", { name: `Удалить ${folder}` }).click();

      await expect(fileManager.page.getByTestId("recursive-warning")).toBeVisible();
    });

    await test.step("после подтверждения папки нет", async () => {
      await fileManager.page.getByRole("button", { name: "Удалить" }).click();

      await expect(fileManager.entryLink(folder)).toHaveCount(0);
    });
  });

  test("переименование папки", async ({ fileManager, workspace }) => {
    const before = uniqueName("было");
    const after = uniqueName("стало");

    await fileManager.createFolder(before);
    await fileManager.renameEntry(before, after);

    await expect(fileManager.status).toContainText("Переименовано");
    await expect(fileManager.entryLink(after)).toBeVisible();
    await expect(fileManager.entryLink(before)).toHaveCount(0);

    await fileManager.goto(workspace);
  });
});
