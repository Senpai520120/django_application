import { expect, test, uniqueName, login, loginAs, logout } from "./support/fixtures";


test.describe("<test group name>", () => {

  test("<test case name1>", async ({ panel, audit }) => {
    // todo: test case 1 implementation
    await login(panel.page);
    await goto()
  });

  test("<test case name2>", async ({ panel, audit, fileManager }) => {
    // todo: test case 2 implementation
  });

});
