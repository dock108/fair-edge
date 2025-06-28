# FairEdge API Reference

Complete API documentation for the FairEdge sports betting analysis platform.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.yourdomain.com`

## Authentication

All protected endpoints require JWT authentication via Supabase.

```bash
# Include Authorization header
Authorization: Bearer <jwt_token>
```

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
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  }
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

## Authentication Endpoints

### Login
```http
POST /auth/login
```

**Body:**
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "role": "basic"
  }
}
```

## Billing Endpoints

### Create Checkout Session
```http
POST /billing/create-checkout-session
```

**Body:**
```json
{
  "price_id": "price_basic_monthly"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/..."
}
```

### Webhook Handler
```http
POST /billing/webhook
```
Stripe webhook endpoint for subscription events.

## Rate Limiting

All endpoints are rate limited:
- **Anonymous**: 30 requests/minute
- **Authenticated**: 60 requests/minute  
- **Premium**: 120 requests/minute

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
- Access to worst 10 opportunities
- -2% EV threshold filter
- Basic endpoints only

### Basic Users  
- All main line opportunities
- Full EV range access
- Standard rate limits

### Premium Users
- All market opportunities
- Advanced analytics access
- Higher rate limits
- Data export capabilities

### Admin Users
- Full system access
- Administrative endpoints
- System metrics access

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

---

For complete interactive API documentation, visit `/docs` when the application is running.