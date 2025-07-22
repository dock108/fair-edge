#!/bin/bash

# Setup Stripe Testing Environment
# This script configures Stripe CLI for webhook forwarding and validates the test environment

set -e  # Exit on any error

echo "🔧 Setting up Stripe testing environment..."

# Check if Stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo "❌ Stripe CLI not found. Please install it first:"
    echo "   brew install stripe/stripe-cli/stripe"
    exit 1
fi

echo "✅ Stripe CLI found"

# Check if logged in to Stripe
if ! stripe config --list &> /dev/null; then
    echo "❌ Not logged in to Stripe. Please run:"
    echo "   stripe login"
    exit 1
fi

echo "✅ Stripe CLI authenticated"

# Validate environment variables
ENV_FILE="../environments/development.env"
if [[ -f "$ENV_FILE" ]]; then
    echo "✅ Development environment file found"

    # Check for required Stripe variables
    if grep -q "STRIPE_SECRET_KEY=sk_test_" "$ENV_FILE" && \
       grep -q "STRIPE_PUBLISHABLE_KEY=pk_test_" "$ENV_FILE" && \
       grep -q "STRIPE_BASIC_PRICE=price_" "$ENV_FILE" && \
       grep -q "STRIPE_PREMIUM_PRICE=price_" "$ENV_FILE"; then
        echo "✅ Stripe test keys configured"
    else
        echo "❌ Missing or invalid Stripe configuration in $ENV_FILE"
        echo "Required variables:"
        echo "  - STRIPE_SECRET_KEY (must start with sk_test_)"
        echo "  - STRIPE_PUBLISHABLE_KEY (must start with pk_test_)"
        echo "  - STRIPE_BASIC_PRICE (must start with price_)"
        echo "  - STRIPE_PREMIUM_PRICE (must start with price_)"
        exit 1
    fi
else
    echo "❌ Development environment file not found: $ENV_FILE"
    exit 1
fi

# Validate Stripe products exist
echo "🔍 Validating Stripe products..."

BASIC_PRICE=$(grep "STRIPE_BASIC_PRICE=" "$ENV_FILE" | cut -d'=' -f2)
PREMIUM_PRICE=$(grep "STRIPE_PREMIUM_PRICE=" "$ENV_FILE" | cut -d'=' -f2)

if stripe prices retrieve "$BASIC_PRICE" &> /dev/null; then
    echo "✅ Basic plan price exists: $BASIC_PRICE"
else
    echo "❌ Basic plan price not found: $BASIC_PRICE"
    exit 1
fi

if stripe prices retrieve "$PREMIUM_PRICE" &> /dev/null; then
    echo "✅ Premium plan price exists: $PREMIUM_PRICE"
else
    echo "❌ Premium plan price not found: $PREMIUM_PRICE"
    exit 1
fi

echo ""
echo "🎉 Stripe testing environment validated!"
echo ""
echo "📋 Next steps:"
echo "1. Start your development server:"
echo "   cd frontend && npm run dev"
echo ""
echo "2. In a separate terminal, start webhook forwarding:"
echo "   stripe listen --forward-to localhost:8000/api/billing/webhook"
echo ""
echo "3. Copy the webhook signing secret from the output and update your .env:"
echo "   STRIPE_WEBHOOK_SECRET=whsec_..."
echo ""
echo "4. Run the test suite:"
echo "   cd frontend && npm run test:e2e"
echo ""
echo "🧪 Test cards to use:"
echo "   Card number: 4242424242424242"
echo "   Expiry: Any future date (e.g., 12/30)"
echo "   CVC: Any 3 digits (e.g., 123)"
echo ""
