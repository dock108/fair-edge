# Sports Betting +EV Analyzer

A modern sports betting analysis tool that identifies positive expected value (EV) betting opportunities across multiple sportsbooks.

## 🏗 Architecture

This application uses a **modern SPA (Single Page Application) architecture**:

- **Frontend**: React TypeScript SPA built with Vite
- **Backend**: FastAPI serving JSON APIs only  
- **Cache**: Redis for high-performance data caching
- **Database**: PostgreSQL with Supabase authentication
- **Background Tasks**: Celery with Redis broker
- **Deployment**: Independent frontend and backend deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Redis (for caching and task queue)
- PostgreSQL (or Supabase account)

### Local Development

```bash
# 1. Start all services (Backend + Redis + Celery)
./scripts/start_local_dev.sh

# 2. Start frontend (separate terminal)
cd frontend && npm install && npm run dev

# 3. Check system status
./scripts/check_status.sh
```

The application will be available at:
- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

### Manual Setup

<details>
<summary>Backend (FastAPI)</summary>

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start Redis (required)
redis-server

# Start Celery worker (background tasks)
celery -A worker worker --loglevel=info

# Start Celery beat (scheduler)  
celery -A worker beat --loglevel=info

# Start API server
uvicorn app:app --reload --port 8000
```
</details>

<details>
<summary>Frontend (React)</summary>

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
</details>

## 🎯 Key Features

- **Real-time EV Analysis**: Live calculation of expected value across multiple sportsbooks
- **Automated Data Refresh**: 5-minute interval updates from odds providers
- **Role-based Access**: Free tier (main lines) vs Premium (all markets) 
- **Recommended Odds**: System provides specific recommended betting odds and books
- **Market Coverage**: Moneyline, spreads, totals, and player props
- **Real-time Updates**: WebSocket connections for live data updates
- **Admin Dashboard**: System monitoring and manual refresh capabilities

## 📊 Data Pipeline

```
The Odds API → FastAPI Processing → Redis Cache → React Frontend
      ↓              ↓                  ↓
   Celery Tasks → EV Analysis → Role-based Filtering
```

The system automatically:
1. Fetches odds data every 5 minutes via Celery
2. Calculates expected value for all betting opportunities  
3. Caches processed data in Redis with role-based segmentation
4. Serves optimized data to React frontend via JSON API

## 📁 Project Structure

```
fairedge/
├── app.py                 # FastAPI application
├── core/                  # Core utilities (auth, settings, etc.)
├── services/              # Business logic services
├── routes/                # API route modules
├── models.py              # Database models
├── utils/                 # Shared utilities
├── tasks/                 # Background task definitions
├── frontend/              # React SPA
├── docs/                  # Detailed documentation
├── scripts/               # Development and setup scripts
├── logs/                  # Application logs
└── .env.example           # Environment configuration template
```

## 🔧 Configuration

### Environment Variables

Key configuration options:

```bash
# Database & Authentication
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# External APIs
ODDS_API_KEY=your-odds-api-key

# Redis
REDIS_URL=redis://localhost:6379/0

# Refresh Settings
REFRESH_INTERVAL_MINUTES=5
```

See `.env.example` for complete configuration options.

## 🚀 Deployment

### Frontend
```bash
cd frontend
npm run build
# Deploy dist/ folder to static hosting (Netlify, Vercel, S3+CloudFront)
```

### Backend
Deploy FastAPI app with:
- Docker containers (recommended)
- AWS EC2/ECS/Lambda
- Railway, Render, or similar platforms

Ensure Redis and PostgreSQL are available and CORS is configured for your frontend domain.

## 📚 Documentation

For comprehensive documentation, see the **[Documentation Index](docs/INDEX.md)**.

**Quick Links:**
- **[Development Guide](docs/DEVELOPMENT.md)** - Complete developer setup and workflows
- **[Database Setup](docs/DB_ENUM_UPGRADES.md)** - Database schema and migrations
- **[UI Layout System](docs/LAYOUT_GUIDE.md)** - Frontend layout and components  
- **[Horizontal Scaling](docs/HORIZONTAL_SCALING.md)** - Production scaling strategies
- **[Testing Guide](docs/TESTING.md)** - Comprehensive testing documentation

## 🧪 Testing

```bash
# Run smoke tests (quick health checks)
./scripts/run_tests.sh smoke

# Run load tests (performance testing)
./scripts/run_tests.sh load

# Run full test suite
./scripts/run_tests.sh integration
```

## 🛠 Development Tools

- **Health Check**: `./scripts/check_status.sh` - Monitor all services
- **Start Services**: `./scripts/start_local_dev.sh` - One-command startup
- **Stop Services**: `./scripts/stop_local_dev.sh` - Clean shutdown
- **Test Environment**: `./scripts/test_setup.py` - Validate dependencies

## 🏛 Technology Stack

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- React Router (client-side routing)
- Axios (HTTP client)
- Bootstrap 5 (styling)

**Backend:**
- FastAPI (Python web framework)
- Celery (background tasks)
- SQLAlchemy (database ORM)
- Redis (caching + task broker)
- Supabase (authentication)

**Infrastructure:**
- PostgreSQL (database)
- Docker (containerization)
- GitHub Actions (CI/CD)

## 📈 Performance

- **API Response Time**: < 200ms for cached data
- **Data Refresh**: Every 5 minutes automatically
- **Concurrent Users**: Tested up to 100 concurrent users
- **Uptime**: 99.9% target with health monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`./scripts/run_tests.sh smoke`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

[MIT License](LICENSE) - see the LICENSE file for details.

---

## 🆘 Troubleshooting

**Common Issues:**

- **Redis Connection Error**: Ensure Redis is running (`redis-server`)
- **API Key Issues**: Check `.env` file for valid `ODDS_API_KEY`
- **Permission Errors**: Run `chmod +x *.sh` to make scripts executable
- **Port Conflicts**: Default ports are 8000 (API), 5173 (frontend), 6379 (Redis)

**Get Help:**
- Check system status: `./scripts/check_status.sh`
- View logs: `tail -f logs/*.log`
- Test setup: `python scripts/test_setup.py` 