# Sports Betting +EV Analyzer

A modern sports betting analysis tool that identifies positive expected value (EV) betting opportunities across multiple sportsbooks.

## Architecture

This application uses a **modern SPA (Single Page Application) architecture**:

- **Frontend**: React TypeScript SPA built with Vite
- **Backend**: FastAPI serving JSON APIs only
- **Deployment**: Independent frontend and backend deployment

## Migration Status: ✅ COMPLETED

This project has been successfully migrated from a Jinja2 template-based frontend to a modern React SPA. The migration is complete and the old template system has been removed.

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- Redis (for caching)

### Backend (FastAPI)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the API server
uvicorn app:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Frontend (React)
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Key Features

- **Real-time EV Analysis**: Live calculation of expected value across multiple sportsbooks
- **Recommended Odds**: System provides specific recommended betting odds and books
- **Market Coverage**: Moneyline, spreads, totals, and player props
- **Role-based Access**: Free tier (main lines) vs Premium (all markets)
- **Real-time Updates**: WebSocket connections for live data updates

## API Endpoints

### Core Endpoints
- `GET /api/opportunities/ui` - Processed betting opportunities (UI-ready)
- `GET /api/session/user` - Current user session info
- `GET /health` - System health check

### Authentication
- `POST /api/session` - Create session
- `POST /api/logout-secure` - Secure logout

### Admin/Premium
- `GET /api/analytics/advanced` - Advanced analytics (subscribers)
- `POST /api/opportunities/refresh` - Manual data refresh (admin)

## Environment Configuration

### Frontend (.env files)
```bash
# .env.development
VITE_API_URL=http://localhost:8000

# .env.production  
VITE_API_URL=https://your-api-domain.com
```

### Backend
Configure via environment variables or settings file for:
- Database connections
- Redis cache settings
- CORS allowed origins
- Authentication providers

## Deployment

### Frontend Deployment
```bash
cd frontend
npm run build
# Deploy dist/ folder to static hosting (Netlify, Vercel, S3+CloudFront)
```

### Backend Deployment
Deploy FastAPI app to your preferred platform:
- Docker containers
- AWS EC2/ECS
- Heroku
- Railway

Ensure CORS is configured for your frontend domain.

## Migration Notes

The application was successfully migrated from Jinja2 templates to React SPA:

- ✅ All UI components converted to React
- ✅ Backend converted to pure JSON API
- ✅ Data processing logic moved to `/api/opportunities/ui` endpoint
- ✅ Authentication and session management preserved
- ✅ Real-time updates via WebSocket maintained
- ✅ Old template files and static assets removed

## Technology Stack

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- React Router (client-side routing)
- Axios (HTTP client)
- Bootstrap 5 (styling)

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (database ORM)
- Redis (caching)
- WebSockets (real-time updates)
- Supabase (authentication)

## License

[Your License Here] 