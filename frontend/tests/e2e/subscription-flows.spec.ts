import { test, expect } from '@playwright/test';
import { faker } from '@faker-js/faker';

// Test configuration - Using pre-confirmed test users
const TEST_FREE_EMAIL = 'test-free@fairedge.com';
const TEST_BASIC_EMAIL = 'test-basic@fairedge.com';
const TEST_PREMIUM_EMAIL = 'test-premium@fairedge.com';
const TEST_PASSWORD = 'TestPassword123!';

// Stripe test card numbers
const STRIPE_TEST_CARD = '4242424242424242';
const STRIPE_TEST_EXPIRY = '12/30';
const STRIPE_TEST_CVC = '123';

test.describe('Subscription Flow Tests', () => {
  test.describe.configure({ mode: 'serial' });

  test('1. Free User Login & Verification', async ({ page }) => {
    // Login with pre-confirmed free user
    await page.goto('/login');
    await page.fill('input#email', TEST_FREE_EMAIL);
    await page.fill('input#password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Check for success (redirect to root dashboard)
    await page.waitForURL('/', { timeout: 15000 });

    // Navigate to pricing to see free tier status
    await page.goto('/pricing');

    // Should show free tier limitations
    await expect(page.getByText(/Only unprofitable bets/i).first()).toBeVisible();
    await expect(page.getByText(/Start 7-Day Free Trial/i).first()).toBeVisible();

    // Navigate to dashboard to verify login success
    await page.goto('/');

    // Verify we're authenticated by checking that login/signup buttons are gone
    await expect(page.locator('a[href="/login"]')).not.toBeVisible();
    await expect(page.locator('a[href="/signup"]')).not.toBeVisible();

    // Verify we have access to authenticated content (Dashboard should be highlighted/active)
    await expect(page.locator('.nav-link.active')).toContainText('Dashboard');
  });

  test('2. Upgrade to Basic Plan (Free → Basic)', async ({ page }) => {
    // Login with the free test user
    await page.goto('/login');
    await page.fill('input#email', TEST_FREE_EMAIL);
    await page.fill('input#password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for login to complete
    await page.waitForURL('/', { timeout: 10000 });

    // Navigate to pricing page
    await page.goto('/pricing');

    // Find and click the Basic plan "Start 7-Day Free Trial" button
    const basicButton = page.getByText('Start 7-Day Free Trial').first();
    await basicButton.click();

    // Wait for Stripe checkout to load (this may be a new tab or redirect)
    await page.waitForURL(/checkout\.stripe\.com/, { timeout: 15000 });

    // On Stripe checkout page, wait for form to load
    await page.waitForSelector('input[name="cardNumber"]', { timeout: 10000 });

    // Fill Stripe checkout form
    await page.fill('input[name="cardNumber"]', STRIPE_TEST_CARD);
    await page.fill('input[name="cardExpiry"]', STRIPE_TEST_EXPIRY);
    await page.fill('input[name="cardCvc"]', STRIPE_TEST_CVC);
    await page.fill('input[name="billingName"]', 'Test User');

    // Submit payment
    await page.click('button[type="submit"]');

    // Wait for redirect back to app (success page)
    await page.waitForURL(/localhost:5173/, { timeout: 30000 });

    // Go to pricing page to verify upgrade
    await page.goto('/pricing');

    // Verify user is now on Basic plan
    await expect(page.getByText(/Current Plan/i)).toBeVisible();
    await expect(page.getByText(/You're enjoying Basic features/i)).toBeVisible();

    // Verify they can now upgrade to Premium
    await expect(page.getByText(/Upgrade to Premium/i)).toBeVisible();
  });

  test('3. Upgrade to Premium Plan (Basic → Premium)', async ({ page }) => {
    // Login with the basic test user (who should now be on basic plan from previous test)
    await page.goto('/login');
    await page.fill('input#email', TEST_FREE_EMAIL);
    await page.fill('input#password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for login to complete
    await page.waitForURL('/', { timeout: 10000 });

    // Navigate to pricing page
    await page.goto('/pricing');

    // Click upgrade to Premium button
    const upgradeButton = page.getByText('Upgrade to Premium');
    await upgradeButton.click();

    // Wait for Stripe checkout to load
    await page.waitForURL(/checkout\.stripe\.com/, { timeout: 15000 });

    // On Stripe checkout page, wait for form to load
    await page.waitForSelector('input[name="cardNumber"]', { timeout: 10000 });

    // Fill Stripe checkout form
    await page.fill('input[name="cardNumber"]', STRIPE_TEST_CARD);
    await page.fill('input[name="cardExpiry"]', STRIPE_TEST_EXPIRY);
    await page.fill('input[name="cardCvc"]', STRIPE_TEST_CVC);
    await page.fill('input[name="billingName"]', 'Test User');

    // Submit payment
    await page.click('button[type="submit"]');

    // Wait for redirect back to app
    await page.waitForURL(/localhost:5173/, { timeout: 30000 });

    // Go to pricing page to verify upgrade to Premium
    await page.goto('/pricing');

    // Verify user is now on Premium plan
    await expect(page.getByText(/Current Plan/i).nth(1)).toBeVisible(); // Second "Current Plan" for Premium
    await expect(page.getByText(/You're enjoying Premium features/i)).toBeVisible();

    // Verify no more upgrade buttons are shown for Premium
    await expect(page.getByText(/Upgrade to Premium/i)).not.toBeVisible();
  });

  test('4. Cancel Subscription (Premium → Free)', async ({ page }) => {
    // Login with the PREMIUM test user for cancellation testing
    await page.goto('/login');
    await page.fill('input#email', TEST_PREMIUM_EMAIL);
    await page.fill('input#password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for login to complete
    await page.waitForURL('/', { timeout: 10000 });

    // Click on user menu dropdown in header
    await page.click('.user-menu-trigger');

    // Click "Manage Subscription" to open Stripe Customer Portal
    await page.click('button:has-text("Manage Subscription")');

    // This will redirect to Stripe Customer Portal
    await page.waitForURL(/billing\.stripe\.com/, { timeout: 15000 });

    // On Stripe Customer Portal, find and click cancel subscription
    await page.waitForSelector('button:has-text("Cancel subscription")', { timeout: 10000 });
    await page.click('button:has-text("Cancel subscription")');

    // Confirm cancellation in the modal/form
    await page.click('button:has-text("Cancel subscription")'); // Confirm button

    // Wait for the portal to show cancellation confirmation
    await expect(page.getByText(/canceled|cancelled/i)).toBeVisible({ timeout: 15000 });

    // Return to the app (there should be a "Return to FairEdge" button)
    await page.click('a:has-text("Return")');

    // Verify user is back to free tier on pricing page
    await page.goto('/pricing');

    // Should see trial buttons again (not "Current Plan")
    await expect(page.getByText(/Start 7-Day Free Trial/i)).toBeVisible();
    await expect(page.getByText(/Current Plan/i)).not.toBeVisible();

    // Check that they see free tier limitations again
    await expect(page.getByText(/Only unprofitable bets/i).first()).toBeVisible();
  });

  test('5. Basic Subscriber Account Verification', async ({ page }) => {
    // Login with pre-configured basic subscriber
    await page.goto('/login');
    await page.fill('input#email', TEST_BASIC_EMAIL);
    await page.fill('input#password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for login to complete
    await page.waitForURL('/', { timeout: 10000 });

    // Verify login success by checking authentication state
    await expect(page.locator('a[href="/login"]')).not.toBeVisible();

    // Test subscription status endpoint directly
    const statusResponse = await page.request.get('/api/billing/subscription-status');

    if (statusResponse.status() !== 200) {
      const errorData = await statusResponse.text();
      console.log('API Error Status:', statusResponse.status());
      console.log('API Error Response:', errorData);
      console.log('Response Headers:', await statusResponse.allHeaders());
    }

    expect(statusResponse.status()).toBe(200);

    const statusData = await statusResponse.json();
    console.log('Basic user status data:', statusData);

    // Verify the user has basic access level
    expect(['basic', 'subscriber'].includes(statusData.role)).toBe(true);
    expect(statusData.is_subscriber || statusData.role === 'basic').toBe(true);
  });

  test('6. Premium Subscriber Account Verification', async ({ page }) => {
    // Login with pre-configured premium subscriber
    await page.goto('/login');
    await page.fill('input#email', TEST_PREMIUM_EMAIL);
    await page.fill('input#password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for login to complete
    await page.waitForURL('/', { timeout: 10000 });

    // Verify login success by checking authentication state
    await expect(page.locator('a[href="/login"]')).not.toBeVisible();

    // Test subscription status endpoint directly
    const statusResponse = await page.request.get('/api/billing/subscription-status');
    expect(statusResponse.status()).toBe(200);

    const statusData = await statusResponse.json();
    console.log('Premium user status data:', statusData);

    // Verify the user has premium access level
    expect(['premium', 'subscriber'].includes(statusData.role)).toBe(true);
    expect(statusData.is_subscriber).toBe(true);
  });

  test('7. API Integration Tests', async ({ page }) => {
    // Login with the test user (should now be free after cancellation)
    await page.goto('/login');
    await page.fill('input#email', TEST_FREE_EMAIL);
    await page.fill('input#password', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // Wait for login to complete
    await page.waitForURL('/', { timeout: 10000 });

    // Test subscription status endpoint
    const statusResponse = await page.request.get('/api/billing/subscription-status');
    expect(statusResponse.status()).toBe(200);

    const statusData = await statusResponse.json();
    expect(statusData.role).toBe('free'); // User should be back to free after cancellation
    expect(statusData.is_subscriber).toBe(false);

    // Test that creating checkout session works for free users
    const checkoutResponse = await page.request.post('/api/billing/create-checkout-session', {
      data: { plan: 'basic' }
    });
    expect(checkoutResponse.status()).toBe(200);

    const checkoutData = await checkoutResponse.json();
    expect(checkoutData.checkout_url).toContain('checkout.stripe.com');

    // Test that premium features are protected for free users
    const premiumResponse = await page.request.get('/api/analytics/advanced');
    expect(premiumResponse.status()).toBe(403);
  });
});

// Helper functions for test setup
export async function setupTestUser(page: any, email: string, password: string) {
  await page.goto('/signup');
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('/dashboard');
}

export async function loginTestUser(page: any, email: string, password: string) {
  await page.goto('/login');
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL('/dashboard');
}

export async function completeStripeCheckout(page: any) {
  await page.waitForURL(/checkout\.stripe\.com/);
  await page.fill('input[name="cardNumber"]', STRIPE_TEST_CARD);
  await page.fill('input[name="cardExpiry"]', STRIPE_TEST_EXPIRY);
  await page.fill('input[name="cardCvc"]', STRIPE_TEST_CVC);
  await page.fill('input[name="billingName"]', 'Test User');
  await page.click('button[type="submit"]');
  await page.waitForURL(/localhost:5173/);
}
