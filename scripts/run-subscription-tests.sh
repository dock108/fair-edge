#!/bin/bash

# Run Subscription Flow Tests
# This script coordinates running the full end-to-end subscription test suite

set -e

echo "🧪 Running FairEdge Subscription Flow Tests"
echo "==========================================="

# Check if we're in the right directory
if [[ ! -f "package.json" ]] || [[ ! -f "playwright.config.ts" ]]; then
    echo "❌ Error: Must be run from the frontend directory"
    echo "   cd frontend && ../scripts/run-subscription-tests.sh"
    exit 1
fi

# Validate Stripe test environment
echo "🔍 Validating Stripe test environment..."
if ! ../scripts/setup-stripe-testing.sh; then
    echo "❌ Stripe environment validation failed"
    exit 1
fi

echo ""
echo "📋 Test Execution Plan:"
echo "1. Start development server (frontend & backend)"
echo "2. Start Stripe webhook forwarding"
echo "3. Run Playwright test suite"
echo "4. Generate test report"
echo ""

# Check if development server is running
echo "🔄 Checking if development server is running..."
if ! curl -s http://localhost:5173 > /dev/null; then
    echo "❌ Frontend development server not running"
    echo "   Please start it in another terminal: npm run dev"
    exit 1
fi

if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend API server not running"
    echo "   Please start it in another terminal: cd .. && docker compose up -d"
    exit 1
fi

echo "✅ Development servers are running"

# Check if Stripe CLI is listening
echo "🎯 Checking Stripe webhook forwarding..."
if pgrep -f "stripe listen" > /dev/null; then
    echo "✅ Stripe webhook forwarding is running"
else
    echo "⚠️  Stripe webhook forwarding not detected"
    echo "   Starting webhook forwarding in background..."

    # Start webhook forwarding in background
    nohup stripe listen --forward-to localhost:8000/api/billing/webhook \
        --events checkout.session.completed,customer.subscription.created,customer.subscription.updated,customer.subscription.deleted \
        > stripe-webhook.log 2>&1 &

    STRIPE_PID=$!
    echo "   Started with PID: $STRIPE_PID"

    # Wait a moment for it to initialize
    sleep 3

    # Check if it's still running
    if kill -0 $STRIPE_PID 2>/dev/null; then
        echo "✅ Webhook forwarding started successfully"
        echo "   Log file: stripe-webhook.log"
    else
        echo "❌ Failed to start webhook forwarding"
        exit 1
    fi
fi

echo ""
echo "🚀 Running Playwright test suite..."
echo "   This will test the complete subscription flow:"
echo "   • Free user signup"
echo "   • Upgrade to Basic plan"
echo "   • Upgrade to Premium plan"
echo "   • Cancel subscription"
echo "   • API integration validation"
echo ""

# Install Playwright browsers if needed (headless)
if ! npm run test:e2e --dry-run &>/dev/null; then
    echo "📦 Installing Playwright browsers..."
    npx playwright install chromium
fi

# Run the tests
echo "🎬 Executing tests..."
if npm run test:e2e; then
    echo ""
    echo "🎉 All subscription tests passed!"
    echo ""
    echo "📊 Test Report:"
    echo "   • View HTML report: npx playwright show-report"
    echo "   • Test artifacts saved in test-results/"
    echo ""
    echo "✅ Your subscription flow is working correctly!"
else
    echo ""
    echo "❌ Some tests failed"
    echo ""
    echo "📊 Debugging:"
    echo "   • View HTML report: npx playwright show-report"
    echo "   • Check test-results/ for screenshots and videos"
    echo "   • Check stripe-webhook.log for webhook events"
    echo "   • Ensure test Stripe keys are configured correctly"
    exit 1
fi

# Cleanup
if [[ -n "$STRIPE_PID" ]]; then
    echo "🧹 Stopping webhook forwarding..."
    kill $STRIPE_PID 2>/dev/null || true
fi

echo ""
echo "✨ Test execution complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Review test results in the HTML report"
echo "2. Fix any failing tests before going live"
echo "3. When ready, proceed to live Stripe configuration"
echo "4. Deploy to production with live keys"
echo ""
