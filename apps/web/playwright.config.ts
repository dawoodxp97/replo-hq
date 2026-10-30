import { defineConfig } from '@playwright/test';

// Critical-path e2e runs against the api + web dev servers (see repo README).
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: { baseURL: process.env.WEB_URL ?? 'http://localhost:3000' },
  webServer: process.env.CI
    ? undefined
    : { command: 'pnpm dev', url: 'http://localhost:3000', reuseExistingServer: true },
});
