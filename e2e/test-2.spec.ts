// import { test, expect } from './support/fixtures';

// test.describe("Files", () => {
//   test("a file survives upload, download and rename, then is deleted", async ({
//     fileManager,
//     workspace,
//   }) => {
//     const file = textFile("notes.txt");
//     const renamed = "notes-renamed.txt";

//     await test.step("the folder starts empty", async () => {
//       await expect(fileManager.entryLink(file.name)).toHaveCount(0);
//     });

//     await test.step("upload puts the file in the listing", async () => {
//       await fileManager.uploadFiles([file]);
//       await expect(fileManager.entryLink(file.name)).toBeVisible();
//     });

//     await test.step("download hands back the same name", async () => {
//       const downloadPromise = fileManager.page.waitForEvent("download");
//       await fileManager.entryLink(file.name).click();
//       const download = await downloadPromise;

//       expect(download.suggestedFilename()).toBe(file.name);
//     });

//     await test.step("rename replaces the old name with the new one", async () => {
//       await fileManager.renameEntry(file.name, renamed);

//       await expect(fileManager.entryLink(renamed)).toBeVisible();
//       await expect(fileManager.entryLink(file.name)).toHaveCount(0);
//     });

//     await test.step("delete removes it from the listing", async () => {
//       await fileManager.deleteEntry(renamed);

//       await expect(fileManager.entryLink(renamed)).toHaveCount(0);
//     });
//   });
// });