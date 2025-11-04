import { test, expect } from '@playwright/test';

test.describe('Tutor Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    // First, get a tutor ID from the list page
    await page.goto('/tutors');
    await page.waitForSelector('table tbody tr', { timeout: 15000 });
    
    // Get the first tutor's link
    const firstRow = page.locator('table tbody tr').first();
    
    if (await firstRow.count() > 0) {
      // Click to navigate to detail page
      await firstRow.click();
      await page.waitForURL(/\/tutors\/[a-f0-9-]+/, { timeout: 10000 });
    } else {
      // Skip test if no tutors available
      test.skip();
    }
  });

  test('should load tutor detail page', async ({ page }) => {
    // Check for tutor name
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should display tutor information', async ({ page }) => {
    // Wait for tutor details to load
    await page.waitForSelector('[class*="card"]', { timeout: 15000 });
    
    // Check for tutor email or stats
    const email = page.locator('text=/@/');
    await expect(email.first()).toBeVisible();
  });

  test('should display reschedule rate chart', async ({ page }) => {
    // Wait for chart section
    await page.waitForSelector('text=Reschedule Rate Trends', { timeout: 15000 });
    
    // Check for chart container (Recharts uses SVG)
    const chart = page.locator('svg');
    await expect(chart.first()).toBeVisible({ timeout: 10000 });
  });

  test('should display statistics cards', async ({ page }) => {
    // Wait for stats cards
    await page.waitForSelector('[class*="card"]', { timeout: 15000 });
    
    // Check for stats cards (should have multiple)
    const cards = page.locator('[class*="card"]');
    await expect(cards.first()).toBeVisible();
  });

  test('should navigate back to tutor list', async ({ page }) => {
    // Click "Back to Tutor List" link
    const backLink = page.locator('a:has-text("Back to Tutor List")');
    await expect(backLink).toBeVisible();
    
    await backLink.click();
    
    // Should navigate back to /tutors
    await expect(page).toHaveURL(/\/tutors/);
  });
});

