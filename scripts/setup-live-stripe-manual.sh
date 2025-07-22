#!/bin/bash

# Manual Live Stripe Setup
# This script guides you through setting up live Stripe configuration

set -e

echo "🎯 Setting Up Live Stripe Configuration (Manual Process)"
echo "======================================================="
echo ""
echo "⚠️  IMPORTANT: This will guide you through setting up LIVE Stripe."
echo "   Real customers will be charged real money after this setup."
echo ""

# Get production domain
echo "📍 Production Domain Configuration"
echo "=================================="
echo "What is your production domain? (e.g., https://dock108.ai)"
read -p "Production domain: " -r PRODUCTION_DOMAIN

if [[ -z "$PRODUCTION_DOMAIN" ]]; then
    echo "❌ Production domain is required"
    exit 1
fi

# Clean domain (remove https:// if present)
CLEAN_DOMAIN=${PRODUCTION_DOMAIN#https://}
CLEAN_DOMAIN=${CLEAN_DOMAIN#http://}

echo "✅ Using domain: $CLEAN_DOMAIN"

# Manual Stripe Dashboard Steps
echo ""
echo "📋 MANUAL STEPS - STRIPE DASHBOARD"
echo "=================================="
echo ""
echo "🔗 Open Stripe Dashboard: https://dashboard.stripe.com/"
echo ""
echo "1. Switch to LIVE MODE (toggle in top-left corner)"
echo ""
echo "2. CREATE PRODUCTS & PRICES:"
echo "   a) Go to Products > Add Product"
echo "   b) Create Basic Plan:"
echo "      • Name: FairEdge Basic"
echo "      • Description: All main betting lines with positive EV opportunities"
echo "      • Price: \$3.99 USD recurring monthly"
echo "      • Save and copy the Price ID (starts with price_...)"
echo ""
echo "   c) Create Premium Plan:"
echo "      • Name: FairEdge Premium"
echo "      • Description: Complete market coverage with player props and alternate lines"
echo "      • Price: \$9.99 USD recurring monthly"
echo "      • Save and copy the Price ID (starts with price_...)"
echo ""
echo "3. GET API KEYS:"
echo "   a) Go to Developers > API Keys"
echo "   b) Make sure you're in LIVE mode"
echo "   c) Copy Publishable Key (pk_live_...)"
echo "   d) Reveal and copy Secret Key (sk_live_...)"
echo ""
echo "4. CREATE WEBHOOK ENDPOINT:"
echo "   a) Go to Developers > Webhooks"
echo "   b) Add endpoint with URL: https://$CLEAN_DOMAIN/api/billing/webhook"
echo "   c) Select events:"
echo "      • checkout.session.completed"
echo "      • customer.subscription.created"
echo "      • customer.subscription.updated"
echo "      • customer.subscription.deleted"
echo "      • invoice.payment_succeeded"
echo "      • invoice.payment_failed"
echo "   d) Add endpoint and copy the Signing Secret (whsec_...)"
echo ""

# Get user input for the created resources
echo "📝 Enter Your Live Stripe Configuration"
echo "======================================"
echo ""

read -p "Basic Plan Price ID (price_...): " -r BASIC_PRICE
read -p "Premium Plan Price ID (price_...): " -r PREMIUM_PRICE
read -p "Live Publishable Key (pk_live_...): " -r PUBLISHABLE_KEY
read -p "Live Secret Key (sk_live_...): " -r SECRET_KEY
read -p "Webhook Signing Secret (whsec_...): " -r WEBHOOK_SECRET

# Validate inputs
if [[ ! "$BASIC_PRICE" =~ ^price_ ]]; then
    echo "❌ Basic price ID must start with 'price_'"
    exit 1
fi

if [[ ! "$PREMIUM_PRICE" =~ ^price_ ]]; then
    echo "❌ Premium price ID must start with 'price_'"
    exit 1
fi

if [[ ! "$PUBLISHABLE_KEY" =~ ^pk_live_ ]]; then
    echo "❌ Publishable key must start with 'pk_live_'"
    exit 1
fi

if [[ ! "$SECRET_KEY" =~ ^sk_live_ ]]; then
    echo "❌ Secret key must start with 'sk_live_'"
    exit 1
fi

if [[ ! "$WEBHOOK_SECRET" =~ ^whsec_ ]]; then
    echo "❌ Webhook secret must start with 'whsec_'"
    exit 1
fi

echo "✅ All credentials validated"

# Update production environment file
echo ""
echo "📝 Updating Production Environment..."
echo "===================================="

# Read current production env and update Stripe settings
PROD_ENV="environments/production.env"

if [[ ! -f "$PROD_ENV" ]]; then
    echo "❌ Production environment file not found: $PROD_ENV"
    exit 1
fi

# Create backup
cp "$PROD_ENV" "${PROD_ENV}.backup.$(date +%Y%m%d-%H%M%S)"
echo "✅ Created backup of production.env"

# Update Stripe configuration (cross-platform sed syntax)
sed -i.bak "s|^STRIPE_PUBLISHABLE_KEY=.*|STRIPE_PUBLISHABLE_KEY=$PUBLISHABLE_KEY|" "$PROD_ENV"
sed -i.bak "s|^STRIPE_SECRET_KEY=.*|STRIPE_SECRET_KEY=$SECRET_KEY|" "$PROD_ENV"
sed -i.bak "s|^STRIPE_WEBHOOK_SECRET=.*|STRIPE_WEBHOOK_SECRET=$WEBHOOK_SECRET|" "$PROD_ENV"
sed -i.bak "s|^STRIPE_BASIC_PRICE=.*|STRIPE_BASIC_PRICE=$BASIC_PRICE|" "$PROD_ENV"
sed -i.bak "s|^STRIPE_PREMIUM_PRICE=.*|STRIPE_PREMIUM_PRICE=$PREMIUM_PRICE|" "$PROD_ENV"

# Update domain settings (cross-platform sed syntax)
sed -i.bak "s|^DOMAIN=.*|DOMAIN=$CLEAN_DOMAIN|" "$PROD_ENV"
sed -i.bak "s|^CHECKOUT_SUCCESS_URL=.*|CHECKOUT_SUCCESS_URL=https://$CLEAN_DOMAIN/upgrade/success|" "$PROD_ENV"
sed -i.bak "s|^CHECKOUT_CANCEL_URL=.*|CHECKOUT_CANCEL_URL=https://$CLEAN_DOMAIN/pricing|" "$PROD_ENV"
sed -i.bak "s|^CORS_ORIGINS=.*|CORS_ORIGINS=https://$CLEAN_DOMAIN|" "$PROD_ENV"
sed -i.bak "s|^API_URL=.*|API_URL=https://$CLEAN_DOMAIN|" "$PROD_ENV"

# Clean up backup files created by sed
rm -f "${PROD_ENV}.bak"

echo "✅ Updated production environment with live Stripe configuration"

# Summary
echo ""
echo "🎉 Live Stripe Configuration Complete!"
echo "====================================="
echo ""
echo "✅ Configuration Summary:"
echo "   • Domain: $CLEAN_DOMAIN"
echo "   • Basic Plan: $BASIC_PRICE (\$3.99/month)"
echo "   • Premium Plan: $PREMIUM_PRICE (\$9.99/month)"
echo "   • Webhook: https://$CLEAN_DOMAIN/api/billing/webhook"
echo "   • Live API Keys: Configured"
echo ""
echo "📁 Files Updated:"
echo "   • environments/production.env (with live Stripe config)"
echo "   • Backup created: ${PROD_ENV}.backup.$(date +%Y%m%d-%H%M%S)"
echo ""
echo "🚀 Ready for Production Deployment!"
echo ""
echo "Next steps:"
echo "1. ./scripts/deploy-live-production.sh"
echo "2. ./scripts/validate-live-deployment.sh"
echo ""
