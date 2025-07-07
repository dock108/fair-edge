# Fair-Edge API Reference

Complete API documentation for the Fair-Edge SaaS sports betting analysis platform.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

**Supabase JWT Authentication** - All protected endpoints require JWT authentication.

```bash
# Include Authorization header
Authorization: Bearer <jwt_token>
```

**How to get JWT token:**
1. Authenticate with Supabase client: `supabase.auth.signInWithPassword()`
2. Extract JWT from session: `session.access_token`
3. Include in API requests as Bearer token

## Public Endpoints

### Health Check
```http
GET /health
```
Returns system health status and dependency checks.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "supabase": "healthy",
    "redis": "healthy",
    "celery": "healthy",
    "stripe": "configured"
  },
  "version": "1.0.0"
}
```

### API Documentation
```http
GET /docs
```
Interactive OpenAPI documentation (Swagger UI).

## Opportunities Endpoints

### Get Opportunities
```http
GET /api/opportunities
```

**Query Parameters:**
- `limit` (int): Maximum opportunities to return
- `min_ev` (float): Minimum EV percentage filter
- `market_type` (string): Filter by market type
- `sport` (string): Filter by sport

**Headers:**
- `Authorization: Bearer <token>` (optional - affects filtering)

**Response:**
```json
{
  "opportunities": [
    {
      "id": "123",
      "event_name": "Team A vs Team B",
      "bet_type": "moneyline",
      "bet_description": "Team A Win",
      "expected_value": 0.045,
      "fair_odds": 2.10,
      "best_odds": 2.20,
      "bookmaker": "Bookmaker X",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "filtered": true,
  "user_role": "free"
}
```

### Real-time Opportunities
```http
GET /api/opportunities/stream
```
Server-Sent Events endpoint for real-time opportunity updates.

## Analytics Endpoints (Premium)

### Advanced Analytics
```http
GET /api/analytics/advanced
```
Requires Premium subscription.

**Response:**
```json
{
  "performance_metrics": {
    "win_rate": 0.65,
    "average_ev": 0.038,
    "roi": 0.12
  },
  "trends": [
    {
      "date": "2024-01-01",
      "opportunities_count": 45,
      "average_ev": 0.042
    }
  ]
}
```

## User Profile Endpoints

### Get User Info
```http
GET /api/user-info
```

**Headers:**
- `Authorization: Bearer <jwt_token>` (required)

**Response:**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "role": "basic",
  "subscription_status": "active",
  "capabilities": {
    "can_access_premium": true,
    "can_export_data": false,
    "max_daily_queries": 1000
  }
}
```

**Note:** Authentication is handled by Supabase client-side. Use `supabase.auth.signInWithPassword()` to get JWT tokens.

## Billing Endpoints

### Create Checkout Session
```http
POST /api/billing/create-checkout-session
```

**Headers:**
- `Authorization: Bearer <jwt_token>` (required)

**Body:**
```json
{
  "plan": "premium"  // "basic" or "premium"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/..."
}
```

**Error Responses:**
```json
// User already subscribed
{
  "error": "bad_request",
  "message": "User is already an active subscriber",
  "code": 400
}

// Stripe not configured
{
  "error": "service_unavailable",
  "message": "Payment processing is not configured. Please contact support.",
  "code": 503
}
```

### Get Subscription Status
```http
GET /api/billing/subscription-status
```

**Headers:**
- `Authorization: Bearer <jwt_token>` (required)

**Response:**
```json
{
  "user_id": "user_uuid",
  "role": "premium",
  "subscription_status": "active",
  "is_subscriber": true,
  "stripe_configured": true
}
```

### Create Customer Portal Session
```http
POST /api/billing/create-portal-session
```

**Headers:**
- `Authorization: Bearer <jwt_token>` (required)

**Rate Limit:** 5 requests/minute

**Requirements:** User must be an active subscriber (basic or premium)

**Response:**
```json
{
  "url": "https://billing.stripe.com/session/..."
}
```

**Features Available in Portal:**
- Update payment methods
- Cancel subscriptions
- View invoices and billing history
- Change subscription plans

### Stripe Webhook Handler
```http
POST /api/billing/stripe/webhook
```

**Internal endpoint** for Stripe webhook events. Not for direct use.

**Handles Events:**
- `checkout.session.completed` - Upgrade user to paid tier
- `customer.subscription.updated` - Handle plan changes
- `customer.subscription.deleted` - Downgrade to free tier
- `invoice.payment_succeeded` - Confirm active subscription
- `invoice.payment_failed` - Handle failed payments

## Rate Limiting

All endpoints are rate limited based on user role:
- **Anonymous**: 30 requests/minute
- **Free Users**: 60 requests/minute
- **Basic Users**: 120 requests/minute
- **Premium Users**: 300 requests/minute
- **Admin Users**: No limits

**Special Endpoints:**
- `/api/billing/create-portal-session`: 5 requests/minute (subscribers only)

Rate limit headers included in responses:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1640995200
```

## Error Responses

Standard HTTP status codes with detailed error messages:

```json
{
  "error": "insufficient_permissions",
  "message": "Premium subscription required for this endpoint",
  "code": 403
}
```

## Role-Based Access

### Free Users
- Access to worst 10 opportunities only
- -2% EV threshold filter applied
- Basic endpoints only
- Limited rate limits

### Basic Users ($3.99/month)
- All main betting lines (moneyline, spreads, totals)
- Unlimited EV access for main lines
- Enhanced filtering and search capabilities
- Standard rate limits
- Email support

### Premium Users ($9.99/month)
- All betting markets including player props
- Advanced analytics and historical data
- Priority data updates and features
- Export capabilities and API access
- Higher rate limits
- Priority support

### Admin Users
- Full system access
- Administrative endpoints
- System metrics access
- User management capabilities

## Data Export (Premium)

### Export Opportunities
```http
GET /api/export/opportunities?format=csv
```

**Query Parameters:**
- `format`: csv, json, xlsx
- `date_from`: ISO date string
- `date_to`: ISO date string

**Response:**
CSV/JSON/Excel file download

## System Endpoints (Admin)

### System Metrics
```http
GET /admin/metrics
```
Prometheus-compatible metrics endpoint.

### User Management
```http
GET /admin/users
POST /admin/users/{user_id}/promote
```

## WebSocket Support

### Real-time Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/opportunities');
ws.onmessage = (event) => {
  const opportunity = JSON.parse(event.data);
  // Handle new opportunity
};
```

## SDK Integration

### Python Client
```python
from fairedge_client import FairEdgeClient

client = FairEdgeClient(
    api_url="http://localhost:8000",
    auth_token="your_jwt_token"
)

opportunities = client.get_opportunities(min_ev=0.02)
```

### JavaScript Client
```javascript
import { FairEdgeAPI } from '@fairedge/client';

const api = new FairEdgeAPI({
  baseURL: 'http://localhost:8000',
  token: 'your_jwt_token'
});

const opportunities = await api.getOpportunities({ minEV: 0.02 });
```

## Subscription Plans

### Basic Plan - $3.99/month
- **Stripe Price ID:** `STRIPE_BASIC_PRICE` environment variable
- **Features:**
  - All main betting lines (moneyline, spreads, totals)
  - Unlimited EV access for main lines
  - Enhanced filtering and search capabilities
  - Email support

### Premium Plan - $9.99/month
- **Stripe Price ID:** `STRIPE_PREMIUM_PRICE` environment variable
- **Features:**
  - All betting markets including player props
  - Advanced analytics and historical data
  - Priority data updates and features
  - Export capabilities and API access
  - Priority support

## Pagination

Large result sets use cursor-based pagination:

```http
GET /api/opportunities?cursor=eyJ0aW1lc3RhbXAiOi...&limit=50
```

**Response includes pagination metadata:**
```json
{
  "data": [...],
  "pagination": {
    "has_more": true,
    "next_cursor": "eyJ0aW1lc3RhbXAiOi...",
    "total_count": 1500
  }
}
```

## Filtering & Sorting

### Advanced Filtering
```http
GET /api/opportunities?filters={"bet_type":["moneyline","spread"],"min_ev":0.03}
```

### Sorting Options
```http
GET /api/opportunities?sort_by=expected_value&sort_order=desc
```

## API Versioning

Current API version: `v1`

Version specified in URL path:
```http
GET /api/v1/opportunities
```

Headers include version information:
```http
X-API-Version: 1.0.0
```

## Architecture Notes

### Database
- **Supabase** for database, authentication, and real-time features
- **No direct PostgreSQL connections** - all operations via Supabase REST API
- Row Level Security (RLS) policies enforce access control

### Payment Processing
- **Stripe** for all payment processing and subscription management
- **Webhook integration** for real-time subscription updates
- **Customer Portal** for self-service billing management

### Authentication Flow
1. Frontend authenticates with Supabase
2. Supabase returns JWT token
3. Frontend includes JWT in API requests
4. Backend validates JWT and fetches user profile
5. Role-based access control applied

## Related Documentation

- [Development Guide](DEVELOPMENT.md) - Local development setup
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Operations Guide](OPERATIONS.md) - Monitoring and maintenance
- [Claude Instructions](CLAUDE.md) - Architecture and troubleshooting

---

For complete interactive API documentation, visit `/docs` when the application is running.