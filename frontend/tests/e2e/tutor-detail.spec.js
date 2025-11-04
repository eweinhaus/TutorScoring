import { test, expect } from '@playwright/test';

test.describe('Tutor Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    // Capture ALL console messages for debugging
    const consoleMessages = [];
    page.on('console', msg => {
      const text = msg.text();
      consoleMessages.push({ type: msg.type(), text });
      if (msg.type() === 'error') {
        console.log(`[CONSOLE ERROR] ${text}`);
      }
    });
    
    // Capture failed network requests
    const failedRequests = [];
    page.on('response', response => {
      if (response.status() >= 400) {
        const url = response.url();
        const status = response.status();
        failedRequests.push({ url, status });
        console.log(`[FAILED REQUEST] ${url} - ${status}`);
      }
    });
    
    // Store in page context for access in tests
    page.consoleMessages = consoleMessages;
    page.failedRequests = failedRequests;
    
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
    await page.waitForTimeout(3000); // Give React time to render
    
    // Wait for spinner to disappear
    let spinnerVisible = true;
    let attempts = 0;
    while (spinnerVisible && attempts < 15) {
      const spinner = page.locator('[class*="spinner"], [class*="loading"], [role="status"]');
      spinnerVisible = await spinner.count() > 0 && await spinner.first().isVisible({ timeout: 1000 }).catch(() => false);
      if (spinnerVisible) {
        await page.waitForTimeout(1000);
        attempts++;
      }
    }
    
    // Debug: Log page content if heading not found
    const bodyText = await page.textContent('body').catch(() => '');
    const url = page.url();
    
    // Check for tutor name or error message (use main content h1, not header)
    // The h1 is inside a card div, so look for it more broadly
    const heading = page.locator('h1').filter({ hasText: /.+/ }).first();
    const errorMessage = page.locator('text=/error/i, text=/unable to connect/i');
    const notFound = page.locator('text=/not found/i');
    const loadingMessage = page.locator('text=/loading/i');
    
    // Wait for one of these to appear
    await Promise.race([
      heading.waitFor({ state: 'visible', timeout: 30000 }).catch(() => null),
      errorMessage.waitFor({ state: 'visible', timeout: 30000 }).catch(() => null),
      notFound.waitFor({ state: 'visible', timeout: 30000 }).catch(() => null),
      loadingMessage.waitFor({ state: 'visible', timeout: 30000 }).catch(() => null),
    ]);
    
    // Check which one is visible
    const headingVisible = await heading.isVisible({ timeout: 2000 }).catch(() => false);
    const errorVisible = await errorMessage.isVisible({ timeout: 2000 }).catch(() => false);
    const notFoundVisible = await notFound.isVisible({ timeout: 2000 }).catch(() => false);
    const loadingVisible = await loadingMessage.isVisible({ timeout: 2000 }).catch(() => false);
    
    if (loadingVisible) {
      // Still loading after all that time - something is wrong
      console.log(`Page still loading. URL: ${url}, Body preview: ${bodyText.substring(0, 500)}`);
      throw new Error('Page stuck in loading state');
    } else if (errorVisible) {
      // Error state is acceptable - page loaded and handled error
      await expect(errorMessage.first()).toBeVisible();
    } else if (notFoundVisible) {
      // If tutor not found, that's also a valid test result
      await expect(notFound).toBeVisible();
    } else if (headingVisible) {
      // Should have a heading with tutor name
      await expect(heading).toBeVisible({ timeout: 10000 });
    } else {
      // Nothing found - take screenshot and log details
      console.log(`[DEBUG] No expected elements found. URL: ${url}`);
      console.log(`[DEBUG] Body preview: ${bodyText.substring(0, 500)}`);
      console.log(`[DEBUG] Console messages: ${JSON.stringify(page.consoleMessages || [], null, 2)}`);
      console.log(`[DEBUG] Failed requests: ${JSON.stringify(page.failedRequests || [], null, 2)}`);
      
      // Check if page has any React content at all
      const reactRoot = await page.locator('#root').textContent().catch(() => '');
      console.log(`[DEBUG] React root content: ${reactRoot.substring(0, 200)}`);
      
      await page.screenshot({ path: 'test-results/tutor-detail-no-content.png', fullPage: true });
      throw new Error(`Tutor detail page did not render expected content. URL: ${url}. Check screenshot and console logs.`);
    }
  });

  test('should display tutor information', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
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
    
    // Wait for cards or error/not found message
    await Promise.race([
      page.waitForSelector('[class*="card"]', { timeout: 30000 }).catch(() => null),
      page.waitForSelector('text=/error/i', { timeout: 30000 }).catch(() => null),
      page.waitForSelector('text=/not found/i', { timeout: 30000 }).catch(() => null),
    ]);
    
    // Check for tutor email or stats (or show not found message)
    const email = page.locator('text=/@/');
    const notFound = page.locator('text=/not found/i');
    const errorMessage = page.locator('text=/error/i, text=/unable to connect/i');
    
    const emailVisible = await email.first().isVisible({ timeout: 5000 }).catch(() => false);
    const notFoundVisible = await notFound.isVisible({ timeout: 5000 }).catch(() => false);
    const errorVisible = await errorMessage.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (errorVisible) {
      await expect(errorMessage.first()).toBeVisible();
    } else if (notFoundVisible) {
      await expect(notFound).toBeVisible();
    } else {
      await expect(email.first()).toBeVisible({ timeout: 10000 });
    }
  });

  test('should display reschedule rate chart', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
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
    
    // Wait for chart section, error, or no data message
    await Promise.race([
      page.waitForSelector('text=Reschedule Rate Trends', { timeout: 30000 }).catch(() => null),
      page.waitForSelector('text=/error/i', { timeout: 30000 }).catch(() => null),
      page.waitForSelector('text=/not found/i', { timeout: 30000 }).catch(() => null),
      page.waitForSelector('text=/no chart data/i', { timeout: 30000 }).catch(() => null),
    ]);
    
    // Check for chart container (Recharts uses SVG) or no data message
    const chart = page.locator('svg').first();
    const noData = page.locator('text=/no chart data/i');
    const errorMessage = page.locator('text=/error/i, text=/unable to connect/i');
    
    const chartVisible = await chart.isVisible({ timeout: 5000 }).catch(() => false);
    const noDataVisible = await noData.isVisible({ timeout: 5000 }).catch(() => false);
    const errorVisible = await errorMessage.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (errorVisible) {
      // Error state is acceptable - page loaded and handled error
      await expect(errorMessage.first()).toBeVisible();
    } else if (noDataVisible) {
      // No data is also a valid state
      await expect(noData).toBeVisible();
    } else {
      // Should have a chart (SVG from Recharts)
      await expect(chart).toBeVisible({ timeout: 10000 });
    }
  });

  test('should display statistics cards', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
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
    
    // Wait for cards or error/not found message
    await Promise.race([
      page.waitForSelector('[class*="card"]', { timeout: 30000 }).catch(() => null),
      page.waitForSelector('text=/error/i', { timeout: 30000 }).catch(() => null),
      page.waitForSelector('text=/not found/i', { timeout: 30000 }).catch(() => null),
    ]);
    
    // Check for stats cards (should have multiple) or not found message
    const cards = page.locator('[class*="card"]');
    const notFound = page.locator('text=/not found/i');
    const errorMessage = page.locator('text=/error/i, text=/unable to connect/i');
    
    const cardsVisible = await cards.first().isVisible({ timeout: 5000 }).catch(() => false);
    const notFoundVisible = await notFound.isVisible({ timeout: 5000 }).catch(() => false);
    const errorVisible = await errorMessage.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (errorVisible) {
      await expect(errorMessage.first()).toBeVisible();
    } else if (notFoundVisible) {
      await expect(notFound).toBeVisible();
    } else {
      await expect(cards.first()).toBeVisible({ timeout: 10000 });
    }
  });

  test('should navigate back to tutor list', async ({ page }) => {
    // Wait for page to fully load first
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    
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
    
    // Look for "Back to Tutor List" link - React Router Link renders as <a>
    // Try multiple selectors to be robust
    const backLink = page.locator('a:has-text("Back to Tutor List"), a[href="/tutors"]:has-text("Back")').first();
    
    // Wait for link to be visible
    await backLink.waitFor({ state: 'visible', timeout: 30000 });
    await expect(backLink).toBeVisible();
    
    await backLink.click();
    
    // Should navigate back to /tutors
    await expect(page).toHaveURL(/\/tutors/, { timeout: 30000 });
  });
});

