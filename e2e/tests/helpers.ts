import { Page, expect } from '@playwright/test';

export const DEMO_EMAIL = 'demo@scriptorium.local';
export const DEMO_PASSWORD = 'scriptorium-demo';

// Read-only user seeded by migration 0007 (role: viewer).
export const VIEWER_EMAIL = 'viewer@scriptorium.local';
export const VIEWER_PASSWORD = 'scriptorium-view';

// BFF API base for direct HTTP (API-level) checks.
export const BFF_BASE_URL = process.env.E2E_BFF_URL ?? 'http://localhost:3001';

export const LEGACY_ADMIN_URL =
  process.env.E2E_LEGACY_ADMIN_URL ?? 'http://localhost:8080/legacy/admin/';
export const LEGACY_ADMIN_USER = process.env.LEGACY_ADMIN_USER ?? 'admin';
export const LEGACY_ADMIN_PASSWORD = process.env.LEGACY_ADMIN_PASSWORD ?? 'scriptorium-dev';

export async function login(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Email').fill(DEMO_EMAIL);
  await page.getByLabel('Password').fill(DEMO_PASSWORD);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/chat$/);
}
