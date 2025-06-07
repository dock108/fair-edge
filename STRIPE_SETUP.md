# 3-Tier Pricing System with Stripe Integration

The pricing page now supports a complete 3-tier system with Stripe integration! Here's the new structure and setup guide.

## New Pricing Tiers

🆓 **Free**: Main lines with -2% EV or worse only (shows ~5-10 unprofitable opportunities daily)  
💙 **Basic ($3.99/month)**: All main lines including positive EV (shows ~15-25 profitable opportunities daily)  
👑 **Premium ($9.99/month)**: Everything + player props & alternate lines (shows ~50-100 opportunities daily)

## What's Been Implemented

✅ **3-Tier Pricing Structure**:
- Free users see only negative EV opportunities (teaser/learning mode)
- Basic users unlock positive EV main lines
- Premium users get complete market access

✅ **Backend Integration**:
- Multiple Stripe price ID support for Basic and Premium
- Role-based user permissions (free/basic/premium)
- Webhook handling for different subscription tiers
- Database updates for proper role assignment

✅ **Frontend Integration**:
- Responsive 3-card pricing layout (1/2/3 cards per row based on screen size)
- Smart upgrade/downgrade buttons based on current subscription
- Comprehensive feature comparison table
- Journey visualization (Free → Basic → Premium)
- Updated FAQ and value propositions

## Setup Instructions

### 1. Environment Configuration

Your `.env` file should include these Stripe settings:

```bash
# Stripe Configuration (Test Mode)
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_BASIC_PRICE=price_your_basic_price_id_here      # $3.99/month
STRIPE_PREMIUM_PRICE=price_your_premium_price_id_here  # $9.99/month
CHECKOUT_SUCCESS_URL=http://localhost:8000/upgrade/success
CHECKOUT_CANCEL_URL=http://localhost:8000/pricing
```

### 2. Stripe Dashboard Setup

1. **Create Stripe Account** (if not done):
   - Go to https://stripe.com and create account
   - Complete verification process

2. **Create Products & Prices**:
   - Go to Products in Stripe Dashboard
   - Create "Basic Subscription" product → Set price to $3.99/month → Copy Price ID
   - Create "Premium Subscription" product → Set price to $9.99/month → Copy Price ID
   - You'll need both Price IDs for the environment variables

3. **Get API Keys**:
   - Go to Developers → API keys
   - Copy Secret key (starts with `sk_test_`)
   - Copy Publishable key (starts with `pk_test_`)

4. **Set up Webhook**:
   - Go to Developers → Webhooks
   - Add endpoint: `http://localhost:8000/api/billing/stripe/webhook`
   - Select events: 
     - `checkout.session.completed`
     - `customer.subscription.deleted`
   - Copy webhook secret (starts with `whsec_`)

### 3. Database Migration

Run the migration to add Stripe columns:

```bash
python scripts/add_stripe_columns.py
```

## How It Works

### User Flow:
1. User clicks "Start 7-Day Free Trial" button
2. If not logged in → redirected to login page
3. If already subscriber → shown "Current Plan" message
4. If free user → creates Stripe checkout session
5. User completes payment on Stripe
6. Webhook updates user role to "subscriber"
7. User redirected to success page

### Key Files Modified:
- `frontend/src/pages/PricingPage.tsx` - Main integration
- `frontend/src/services/apiService.ts` - API methods
- `frontend/src/App.tsx` - Success page route
- `frontend/src/pages/LoginPage.tsx` - Handle redirects

## Testing

### Test with Stripe Test Cards:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- Use any future date for expiry
- Use any 3-digit CVC

### Test Flow:
1. Start the application
2. Go to `/pricing`
3. Click "Start 7-Day Free Trial"
4. Login if needed
5. Complete checkout with test card
6. Verify redirect to success page
7. Check user role updated in database

## Troubleshooting

### Common Issues:

1. **"Payment processing not configured"**:
   - Check all Stripe environment variables are set
   - Verify API keys are valid

2. **Webhook not working**:
   - Check webhook endpoint URL
   - Verify webhook secret matches
   - Check server logs for errors

3. **User role not updating**:
   - Check webhook is receiving events
   - Verify database migration ran successfully
   - Check user email matches in webhook data

### Logs to Check:
- Backend: `logs/celery_worker.log` and app logs
- Frontend: Browser console for API errors
- Stripe: Webhook delivery logs in dashboard

## Production Considerations

When going live:
1. Switch to live Stripe keys
2. Update webhook endpoint to production URL
3. Update success/cancel URLs
4. Test with real payment methods
5. Monitor webhook delivery

That's it! The integration is complete and ready for testing. 🎉 