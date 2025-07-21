# Phase 3: Manual Testing Checklist & Guide

## 🎯 Current Status
- ✅ Phase 1: Test infrastructure setup (completed)
- ✅ Phase 2: Development environment testing (completed)
- 🔄 Phase 3: Manual testing for production readiness (in progress)

## 📋 Remaining Phase 3 Tasks

### 1. **Manual Stripe Integration Testing** 🔄
After backend fixes are implemented, you need to:

#### A. Test Stripe Webhook Forwarding
```bash
# In terminal 1: Start webhook forwarding
cd /Users/michaelfuscoletti/Desktop/fair-edge
./scripts/start-webhook-forwarding.sh

# Copy the webhook signing secret displayed
# Update your .env with the new STRIPE_WEBHOOK_SECRET
```

#### B. Manual Subscription Flow Testing
1. **Free → Basic Upgrade**
   - [ ] Login as `test-free@fairedge.com`
   - [ ] Navigate to `/pricing`
   - [ ] Click "Start 7-Day Free Trial" on Basic plan
   - [ ] Complete Stripe checkout with test card `4242 4242 4242 4242`
   - [ ] Verify redirect to success page
   - [ ] Verify user role updated to 'basic' in database
   - [ ] Verify webhook received in terminal

2. **Basic → Premium Upgrade**
   - [ ] Login as `test-basic@fairedge.com`
   - [ ] Navigate to `/pricing`
   - [ ] Click "Upgrade to Premium"
   - [ ] Complete Stripe checkout
   - [ ] Verify role updated to 'premium'/'subscriber'
   - [ ] Verify access to premium features

3. **Subscription Cancellation**
   - [ ] Login as premium user
   - [ ] Click user menu → "Manage Subscription"
   - [ ] In Stripe Customer Portal, cancel subscription
   - [ ] Verify webhook processes cancellation
   - [ ] Verify user downgraded to 'free' role

### 2. **Production Environment Validation** 📦

#### A. Environment Variable Checklist
```bash
# Verify all production variables are set:
- [ ] STRIPE_SECRET_KEY (live key starting with sk_live_)
- [ ] STRIPE_PUBLISHABLE_KEY (live key starting with pk_live_)
- [ ] STRIPE_WEBHOOK_SECRET (from Stripe dashboard)
- [ ] STRIPE_BASIC_PRICE (price_xxx for Basic plan)
- [ ] STRIPE_PREMIUM_PRICE (price_xxx for Premium plan)
- [ ] SUPABASE_URL
- [ ] SUPABASE_ANON_KEY
- [ ] SUPABASE_SERVICE_ROLE_KEY
- [ ] SUPABASE_JWT_SECRET
- [ ] DATABASE_URL (if using direct connections)
```

#### B. Stripe Dashboard Configuration
1. **Webhook Endpoint Setup**
   - [ ] Add webhook endpoint: `https://api.yourdomain.com/api/billing/stripe/webhook`
   - [ ] Select events:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
   - [ ] Copy webhook signing secret to production env

2. **Customer Portal Configuration**
   - [ ] Enable Customer Portal in Stripe Dashboard
   - [ ] Configure allowed actions (cancel, update payment)
   - [ ] Set branding to match your site

3. **Product & Price Verification**
   - [ ] Verify Basic product/price exists
   - [ ] Verify Premium product/price exists
   - [ ] Confirm price IDs match environment variables

### 3. **Live Payment Testing** 💳

**⚠️ WARNING: This will charge real money! Use a company test card or small amount.**

1. **Test Real Payment Flow**
   - [ ] Create new account with personal email
   - [ ] Attempt Basic plan subscription
   - [ ] Use real credit card (will be charged $3.99)
   - [ ] Verify subscription activates
   - [ ] Immediately cancel to get refund

2. **Test Failed Payment Handling**
   - [ ] Use test card `4000 0000 0000 0341` (declines)
   - [ ] Verify graceful error handling
   - [ ] Check user remains on free tier

### 4. **Performance & Security Validation** 🔒

1. **Rate Limiting Tests**
   - [ ] Verify `/api/billing/create-checkout-session` rate limited
   - [ ] Verify `/api/billing/create-portal-session` rate limited
   - [ ] Test webhook endpoint can handle rapid requests

2. **Security Validation**
   - [ ] Verify webhook signature validation works
   - [ ] Test invalid webhook signatures are rejected
   - [ ] Confirm no PII logged in production
   - [ ] Verify HTTPS enforced on all billing endpoints

### 5. **Monitoring & Alerting Setup** 📊

1. **Stripe Dashboard Monitoring**
   - [ ] Set up failed payment alerts
   - [ ] Configure dispute notifications
   - [ ] Enable fraud detection rules

2. **Application Monitoring**
   - [ ] Verify billing events logged properly
   - [ ] Set up alerts for webhook failures
   - [ ] Monitor subscription conversion rates
   - [ ] Track failed checkout attempts

### 6. **Documentation & Handoff** 📚

1. **User Documentation**
   - [ ] Create subscription FAQ
   - [ ] Document refund policy
   - [ ] Add billing support contact info

2. **Admin Documentation**
   - [ ] Document manual subscription management
   - [ ] Create runbook for common issues
   - [ ] Document Stripe dashboard access

## 🚀 Final Production Deployment Checklist

Before going live with payments:

- [ ] All manual tests passed
- [ ] Stripe webhook endpoint verified working
- [ ] Customer portal properly configured
- [ ] Rate limiting enabled on billing endpoints
- [ ] Error monitoring configured
- [ ] Support documentation ready
- [ ] Rollback plan documented
- [ ] Team trained on billing support

## 📝 Notes & Issues to Track

### Known Issues:
1. Backend database layer needs refactoring (get_db() throws RuntimeError)
2. Playwright tests need auth context fixes
3. User role sync between Supabase and backend needs validation

### Test User Credentials:
- Free: `test-free@fairedge.com` / `TestPassword123!`
- Basic: `test-basic@fairedge.com` / `TestPassword123!`
- Premium: `test-premium@fairedge.com` / `TestPassword123!`

### Important URLs:
- Stripe Dashboard: https://dashboard.stripe.com
- Stripe Webhook Logs: https://dashboard.stripe.com/webhooks
- Production API: https://api.yourdomain.com
- Production App: https://app.yourdomain.com

---

**Last Updated**: [Current Date]
**Next Steps**: Fix backend architecture issues, then complete manual testing
