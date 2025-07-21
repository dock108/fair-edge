#!/bin/bash

# Start Stripe webhook forwarding for testing
# This script starts webhook forwarding and captures the signing secret

set -e

echo "🔗 Starting Stripe webhook forwarding..."

# Check if Stripe CLI is installed and authenticated
if ! command -v stripe &> /dev/null; then
    echo "❌ Stripe CLI not found. Please install it first."
    exit 1
fi

# Start webhook forwarding and capture output
echo "📡 Forwarding webhooks to http://localhost:8000/api/billing/webhook"
echo "💡 Make sure your FastAPI server is running on port 8000"
echo ""
echo "⚠️  Important: Copy the webhook signing secret from the output below"
echo "   and update your .env file with: STRIPE_WEBHOOK_SECRET=whsec_..."
echo ""
echo "🔄 Starting forwarding (press Ctrl+C to stop)..."
echo ""

# Forward webhooks to the billing endpoint
stripe listen --forward-to localhost:8000/api/billing/stripe/webhook \
    --events checkout.session.completed,customer.subscription.created,customer.subscription.updated,customer.subscription.deleted
