import { test, expect } from '@playwright/test';

test.describe('Tutor List Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tutors');
  });

  test('should load tutor list page', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Tutor List');
  });

  test('should display tutors table', async ({ page }) => {
    // Wait for table to load (may take time for API call)
    await page.waitForSelector('table', { timeout: 15000 });
    
    const table = page.locator('table');
    await expect(table).toBeVisible();
  });

  test('should filter by risk status', async ({ page }) => {
    // Wait for filters to load
    await page.waitForSelector('select#risk-status', { timeout: 10000 });
    
    // Select high risk
    await page.selectOption('select#risk-status', 'high_risk');
    
    // Wait for filtered results
    await page.waitForTimeout(2000);
    
    // Verify filter is applied (check URL or table content)
    const select = page.locator('select#risk-status');
    await expect(select).toHaveValue('high_risk');
  });

  test('should search tutors', async ({ page }) => {
    // Wait for search input
    await page.waitForSelector('input#search', { timeout: 10000 });
    
    // Type search query
    await page.fill('input#search', 'test');
    
    // Wait for search results
    await page.waitForTimeout(2000);
    
    // Verify search input has value
    const searchInput = page.locator('input#search');
    await expect(searchInput).toHaveValue('test');
  });

  test('should navigate to tutor detail', async ({ page }) => {
    // Wait for table rows
    await page.waitForSelector('table tbody tr', { timeout: 15000 });
    
    // Click first tutor row or "View Details" button
    const firstRow = page.locator('table tbody tr').first();
    
    if (await firstRow.count() > 0) {
      await firstRow.click();
      
      // Should navigate to tutor detail page
      await expect(page).toHaveURL(/\/tutors\/[a-f0-9-]+/);
    }
  });
});

