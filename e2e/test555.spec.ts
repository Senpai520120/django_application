import { expect, test, uniqueName, login, loginAs, logout } from "./support/fixtures";


test.describe("<test group name>", () => {

  test("<test case name1>", async ({ panel, audit }) => {
    // todo: test case 1 implementation
    const username = "testuser_" + Math.random().toString(36).substring(2, 8);

    await panel.page.getByRole('link', { name: 'Users', exact: true }).click();
    await panel.openCreateUser();
    await panel.fillNewUser({
      username: username,
      password: "TestPassword123",})
    await panel.clickCreate();
    await panel.setRoles(username, ["user"]);
    await panel.gotoAudit();
    const auditRow = await panel.lastAuditRow;
    await expect(auditRow.getByRole("cell", { name: username, exact: true })).toBeVisible();
    await expect(auditRow.getByRole("cell", { name: "granted", exact: true })).toBeVisible();
    await expect(auditRow.getByRole("cell", { name: "user", exact: true })).toBeVisible();

  });

});
