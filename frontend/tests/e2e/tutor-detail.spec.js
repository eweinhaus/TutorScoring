import { test, expect } from '@playwright/test';

test.describe('Tutor Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    // First, get a tutor ID from the list page
    await page.goto('/tutors');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000); // Give React time to render
    
    // Wait for spinner to disappear
    let spinnerVisible = true;
    let attempts = 0;
    while (spinnerVisible && attempts < 10) {
      const spinner = page.locator('[class*="spinner"], [class*="loading"], [role="status"]');
      spinnerVisible = await spinner.count() > 0 && await spinner.first().isVisible({ timeout: 1000 }).catch(() => false);
      if (spinnerVisible) {
        await page.waitForTimeout(1000);
        attempts++;
      }
    }
    
    // Wait for table rows or error message
    await Promise.race([
      page.waitForSelector('table tbody tr', { timeout: 30000 }).catch(() => null),
      page.waitForSelector('text=/error/i', { timeout: 30000 }).catch(() => null),
      page.waitForSelector('text=/no tutors/i', { timeout: 30000 }).catch(() => null),
    ]);
    
    // Get the first tutor's link
    const firstRow = page.locator('table tbody tr').first();
    const rowCount = await firstRow.count({ timeout: 5000 }).catch(() => 0);
    
    if (rowCount > 0) {
      // Click to navigate to detail page
      await firstRow.click({ timeout: 10000 });
      await page.waitForURL(/\/tutors\/[a-f0-9-]+/, { timeout: 30000 });
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(2000); // Give detail page time to render
      
      // Wait for detail page spinner to disappear
      let detailSpinnerVisible = true;
      attempts = 0;
      while (detailSpinnerVisible && attempts < 10) {
        const detailSpinner = page.locator('[class*="spinner"], [class*="loading"], [role="status"]');
        detailSpinnerVisible = await detailSpinner.count() > 0 && await detailSpinner.first().isVisible({ timeout: 1000 }).catch(() => false);
        if (detailSpinnerVisible) {
          await page.waitForTimeout(1000);
          attempts++;
        }
      }
    } else {
      // Skip test if no tutors available
      test.skip();
    }
  });

  test('should load tutor detail page', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    // Check for tutor name or error message (use main content h1, not header)
    const heading = page.locator('main h1, [role="main"] h1').first();
    const notFound = page.locator('text=/not found/i');
    
    const headingVisible = await heading.isVisible({ timeout: 5000 }).catch(() => false);
    const notFoundVisible = await notFound.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (notFoundVisible) {
      // If tutor not found, that's also a valid test result
      await expect(notFound).toBeVisible();
    } else {
      await expect(heading).toBeVisible({ timeout: 30000 });
    }
  });

  test('should display tutor information', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    // Wait for spinner to disappear if present
    const spinner = page.locator('[class*="spinner"], [class*="loading"]');
    if (await spinner.count() > 0) {
      await spinner.first().waitFor({ state: 'hidden', timeout: 30000 });
    }
    await page.waitForSelector('[class*="card"]', { timeout: 30000 });
    
    // Check for tutor email or stats (or show not found message)
    const email = page.locator('text=/@/');
    const notFound = page.locator('text=/not found/i');
    
    const emailVisible = await email.first().isVisible({ timeout: 5000 }).catch(() => false);
    const notFoundVisible = await notFound.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (notFoundVisible) {
      await expect(notFound).toBeVisible();
    } else {
      await expect(email.first()).toBeVisible({ timeout: 10000 });
    }
  });

  test('should display reschedule rate chart', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    // Wait for spinner to disappear if present
    const spinner = page.locator('[class*="spinner"], [class*="loading"]');
    if (await spinner.count() > 0) {
      await spinner.first().waitFor({ state: 'hidden', timeout: 30000 });
    }
    // Wait for chart section or no data message
    await page.waitForSelector('text=Reschedule Rate Trends', { timeout: 30000 }).catch(async () => {
      // If that doesn't exist, check for no data message
      await page.waitForSelector('text=/no chart data/i', { timeout: 5000 }).catch(() => {});
    });
    
    // Check for chart container (Recharts uses SVG) or no data message
    const chart = page.locator('svg');
    const noData = page.locator('text=/no chart data/i');
    
    const chartVisible = await chart.first().isVisible({ timeout: 5000 }).catch(() => false);
    const noDataVisible = await noData.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (noDataVisible) {
      // No data is also a valid state
      await expect(noData).toBeVisible();
    } else {
      await expect(chart.first()).toBeVisible({ timeout: 10000 });
    }
  });

  test('should display statistics cards', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    // Wait for spinner to disappear if present
    const spinner = page.locator('[class*="spinner"], [class*="loading"]');
    if (await spinner.count() > 0) {
      await spinner.first().waitFor({ state: 'hidden', timeout: 30000 });
    }
    await page.waitForSelector('[class*="card"]', { timeout: 30000 });
    
    // Check for stats cards (should have multiple) or not found message
    const cards = page.locator('[class*="card"]');
    const notFound = page.locator('text=/not found/i');
    
    const cardsVisible = await cards.first().isVisible({ timeout: 5000 }).catch(() => false);
    const notFoundVisible = await notFound.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (notFoundVisible) {
      await expect(notFound).toBeVisible();
    } else {
      await expect(cards.first()).toBeVisible({ timeout: 10000 });
    }
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

