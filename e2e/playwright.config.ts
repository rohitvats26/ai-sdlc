import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://localhost:5000',
    trace: 'on-first-retry',
    headless: false,
    launchOptions: {
      slowMo: 1000,
    },
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'mvn -q -f ../pom.xml spring-boot:run',
    url: 'http://localhost:5000',
    reuseExistingServer: true,
    timeout: 180_000,
  },
});
