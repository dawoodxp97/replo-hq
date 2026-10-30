import { expect, test } from '@playwright/test';

// Critical path: sign in → submit a repo → watch generation → open the
// tutorial → answer a quiz question. Requires the api (:8000), worker and
// web (:3000) dev servers; the API must be seeded with a test user.
const EMAIL = process.env.E2E_EMAIL ?? 'e2e@example.com';
const PASSWORD = process.env.E2E_PASSWORD ?? 'e2e-password-123';

test('generate and read a tutorial end to end', async ({ page }) => {
  await page.goto('/login');
  await page.getByPlaceholder('Email').fill(EMAIL);
  await page.getByPlaceholder('Password').fill(PASSWORD);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Library' })).toBeVisible();

  await page.goto('/generate');
  await page.getByPlaceholder('https://github.com/org/repo').fill('https://github.com/octocat/Hello-World');
  await page.getByRole('button', { name: 'Generate' }).click();

  await expect(page.getByText('Generating tutorial')).toBeVisible({ timeout: 30_000 });
  await expect(page).toHaveURL(/\/tutorials\//, { timeout: 120_000 });

  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  const markComplete = page.getByRole('button', { name: 'Mark complete' });
  if (await markComplete.count()) await markComplete.click();
  await expect(page.getByRole('button', { name: 'Mark incomplete' })).toBeVisible();
});
