import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');
  });

  test('should load dashboard page', async ({ page }) => {
    // Wait for page to load (don't wait for networkidle due to polling)
    await page.waitForLoadState('domcontentloaded');
    // Check page title or heading (use more specific selector - main content h1, not header)
    const dashboardHeading = page.locator('main h1, [role="main"] h1').first();
    await expect(dashboardHeading).toContainText('Dashboard', { timeout: 30000 });
  });

  test('should display summary cards', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    // Wait for spinner to disappear if present
    const spinner = page.locator('[class*="spinner"], [class*="loading"]');
    if (await spinner.count() > 0) {
      await spinner.first().waitFor({ state: 'hidden', timeout: 30000 });
    }
    await page.waitForSelector('[class*="card"]', { timeout: 30000 });
    
    // Check for summary statistics
    const cards = page.locator('[class*="card"]');
    await expect(cards.first()).toBeVisible({ timeout: 5000 });
  });

  test('should navigate to tutor list', async ({ page }) => {
    // Click on "View All Tutors" link
    const link = page.locator('a:has-text("View All Tutors")');
    await link.click();
    
    // Should navigate to /tutors
    await expect(page).toHaveURL(/\/tutors/);
  });
});

