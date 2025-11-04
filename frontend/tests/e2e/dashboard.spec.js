import { test, expect } from '@playwright/test';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');
  });

  test('should load dashboard page', async ({ page }) => {
    // Check page title or heading
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('should display summary cards', async ({ page }) => {
    // Wait for cards to load
    await page.waitForSelector('[class*="card"]', { timeout: 10000 });
    
    // Check for summary statistics
    const cards = page.locator('[class*="card"]');
    await expect(cards.first()).toBeVisible();
  });

  test('should navigate to tutor list', async ({ page }) => {
    // Click on "View All Tutors" link
    const link = page.locator('a:has-text("View All Tutors")');
    await link.click();
    
    // Should navigate to /tutors
    await expect(page).toHaveURL(/\/tutors/);
  });
});

