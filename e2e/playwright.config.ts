import { defineConfig, devices } from "@playwright/test";

/**
 * Приложение поднимается тем же docker-compose, что и для остального проекта,
 * поэтому адрес приходит снаружи: локально — 127.0.0.1:8000, в CI — тот же
 * стек, при желании — задеплоенное в AWS окружение.
 */
const baseURL = process.env.BASE_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  testDir: ".",
  testMatch: /.*\.spec\.ts/,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  // Локально ретраев нет: флейк должен быть виден сразу, а не прятаться.
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: process.env.CI
    ? [["html", { open: "never" }], ["github"], ["list"]]
    : [["html", { open: "never" }], ["list"]],
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 15_000,
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
