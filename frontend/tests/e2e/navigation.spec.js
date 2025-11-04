import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate between pages', async ({ page }) => {
    // Start at dashboard
    await page.goto('/');
    await expect(page).toHaveURL('/');
    
    // Navigate to tutors via header
    await page.click('a:has-text("Tutors")');
    await expect(page).toHaveURL('/tutors');
    
    // Navigate back to dashboard via header
    await page.click('a:has-text("Dashboard")');
    await expect(page).toHaveURL('/');
  });

  test('should have active navigation state', async ({ page }) => {
    await page.goto('/');
    
    // Check dashboard link is active
    const dashboardLink = page.locator('a:has-text("Dashboard")');
    await expect(dashboardLink).toHaveClass(/bg-primary/);
    
    // Navigate to tutors
    await page.click('a:has-text("Tutors")');
    
    // Check tutors link is active
    const tutorsLink = page.locator('a:has-text("Tutors")');
    await expect(tutorsLink).toHaveClass(/bg-primary/);
  });

  test('should have mobile menu on small screens', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/');
    
    // Check for mobile menu button
    const menuButton = page.locator('button[aria-label="Toggle menu"]');
    await expect(menuButton).toBeVisible();
    
    // Click menu button
    await menuButton.click();
    
    // Check menu is visible
    const mobileMenu = page.locator('text=Dashboard').nth(1);
    await expect(mobileMenu).toBeVisible();
  });
});

