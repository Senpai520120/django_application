import { expect, test, uniqueName } from "./support/fixtures";

/** Лимит приложения. В CI задаётся тем же значением, что и в docker-compose. */
const maxFileSize = Number(process.env.E2E_MAX_FILE_SIZE ?? 5 * 1024 * 1024);

function textFile(name: string, content: string) {
  return { name, mimeType: "text/plain", buffer: Buffer.from(content, "utf-8") };
}

test.describe("Файлы", () => {
  test("загрузка файла и его появление в списке", async ({
    fileManager,
    workspace,
  }) => {
    const name = `${uniqueName("отчёт")}.txt`;

    await fileManager.uploadFiles([textFile(name, "содержимое отчёта")]);

    await expect(fileManager.status).toContainText("Загружено файлов: 1");
    await expect(fileManager.entryLink(name)).toBeVisible();
    await expect(fileManager.row(name)).toContainText("файл");

    await fileManager.goto(workspace);
  });

  test("загрузка нескольких файлов за раз", async ({ fileManager, workspace }) => {
    const first = `${uniqueName("первый")}.txt`;
    const second = `${uniqueName("второй")}.txt`;

    await fileManager.uploadFiles([
      textFile(first, "раз"),
      textFile(second, "два"),
    ]);

    await expect(fileManager.status).toContainText("Загружено файлов: 2");
    await expect(fileManager.entryLink(first)).toBeVisible();
    await expect(fileManager.entryLink(second)).toBeVisible();

    await fileManager.goto(workspace);
  });

  test("переименование файла", async ({ fileManager, workspace }) => {
    const before = `${uniqueName("до")}.txt`;
    const after = `${uniqueName("после")}.txt`;

    await fileManager.uploadFiles([textFile(before, "данные")]);
    await fileManager.renameEntry(before, after);

    await expect(fileManager.entryLink(after)).toBeVisible();
    await expect(fileManager.entryLink(before)).toHaveCount(0);

    await fileManager.goto(workspace);
  });

  test("скачивание файла", async ({ fileManager, workspace }) => {
    const name = `${uniqueName("скачать")}.txt`;
    await fileManager.uploadFiles([textFile(name, "полезная нагрузка")]);

    const download = await test.step("кликаем по имени файла", async () => {
      const waiter = fileManager.page.waitForEvent("download");
      await fileManager.entryLink(name).click();
      return waiter;
    });

    expect(download.suggestedFilename()).toBe(name);

    await fileManager.goto(workspace);
  });

  test("удаление файла с подтверждением", async ({ fileManager, workspace }) => {
    const name = `${uniqueName("удалить")}.txt`;
    await fileManager.uploadFiles([textFile(name, "данные")]);

    await test.step("сначала отменяем", async () => {
      await fileManager.deleteEntry(name, false);
      await expect(fileManager.entryLink(name)).toBeVisible();
    });

    await test.step("потом подтверждаем", async () => {
      await fileManager.deleteEntry(name);
      await expect(fileManager.entryLink(name)).toHaveCount(0);
    });

    await fileManager.goto(workspace);
  });

  test("файл больше лимита отклоняется с понятной ошибкой", async ({
    fileManager,
    workspace,
  }) => {
    const name = `${uniqueName("огромный")}.bin`;
    const oversized = Buffer.alloc(maxFileSize + 1024, 1);

    await fileManager.uploadFiles([
      { name, mimeType: "application/octet-stream", buffer: oversized },
    ]);

    await expect(fileManager.status).toContainText("больше допустимых");
    await expect(fileManager.entryLink(name)).toHaveCount(0);

    await fileManager.goto(workspace);
  });

  test("файл с уже занятым именем не перезаписывает существующий", async ({
    fileManager,
    workspace,
  }) => {
    const name = `${uniqueName("дубль")}.txt`;

    await fileManager.uploadFiles([textFile(name, "первая версия")]);
    await fileManager.uploadFiles([textFile(name, "вторая версия")]);

    await expect(fileManager.status).toContainText("уже существует");
    await expect(fileManager.entryLink(name)).toHaveCount(1);

    await fileManager.goto(workspace);
  });
});
