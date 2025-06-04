# Bet Intel - TurboRepo Monorepo

A modern sports betting analysis platform built with Next.js 15 (React 19) frontend and FastAPI backend.

## 🏗️ Architecture

```
bet-intel/
├── apps/
│   ├── web/          # Next.js 15 frontend (React 19)
│   └── api/          # FastAPI backend + Celery workers
├── packages/
│   ├── ui/           # Shared React components (optional)
│   └── config/       # Shared tooling configs (ESLint, Prettier, TypeScript)
├── turbo.json        # Turbo pipeline configuration
└── package.json      # Root workspace configuration
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- Python 3.12+
- pnpm 9+
- Redis (for caching and Celery)
- PostgreSQL (for data storage)

### Development

1. **Install dependencies:**
   ```bash
   pnpm install
   ```

2. **Start all services:**
   ```bash
   pnpm dev
   ```
   This runs:
   - Next.js frontend on http://localhost:3000
   - FastAPI backend on http://localhost:8000

3. **Start Celery worker (separate terminal):**
   ```bash
   cd apps/api
   celery -A worker.celery worker --loglevel=info
   ```

### Production with Docker

```bash
docker-compose up --build
```

## 📦 Available Scripts

- `pnpm dev` - Start all apps in development mode
- `pnpm build` - Build all apps for production
- `pnpm lint` - Lint all packages
- `pnpm test` - Run tests across all packages
- `pnpm typecheck` - Type check TypeScript files
- `pnpm clean` - Clean build artifacts

## 🛠️ Tech Stack

### Frontend (`apps/web`)
- **Next.js 15** with App Router
- **React 19** with Server Components
- **TypeScript** for type safety
- **Tailwind CSS** with custom design tokens
- **TanStack Query** for server state management
- **Zustand** for client state management
- **Heroicons** for icons

### Backend (`apps/api`)
- **FastAPI** for API endpoints
- **Celery** for background tasks
- **Redis** for caching and task queue
- **SQLAlchemy** with async support
- **Supabase** for authentication
- **Stripe** for payments

### Tooling
- **TurboRepo** for monorepo management
- **pnpm** for package management
- **ESLint** + **Prettier** for code quality
- **Docker** for containerization

## 🔧 Configuration

### Environment Variables

**Frontend (`apps/web/.env.local`):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend (`apps/api/.env`):**
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/betintel
REDIS_URL=redis://localhost:6379
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
STRIPE_SECRET_KEY=your_stripe_secret_key
```

## 🏃‍♂️ Development Workflow

1. **Frontend development:**
   ```bash
   cd apps/web
   pnpm dev
   ```

2. **Backend development:**
   ```bash
   cd apps/api
   pnpm dev  # or: uvicorn main:app --reload
   ```

3. **Add dependencies:**
   ```bash
   # Frontend
   pnpm add -F @betintel/web <package>
   
   # Backend
   cd apps/api && pip install <package> && pip freeze > requirements.txt
   ```

## 🧪 Testing

- **Frontend:** Jest + React Testing Library
- **Backend:** PyTest
- **E2E:** Playwright (planned)

## 📊 Monitoring

- Health checks: `/health` (API) and `/api/health` (Web)
- Prometheus metrics (API)
- Structured logging with correlation IDs

## 🚢 Deployment

The application is containerized and ready for deployment on any Docker-compatible platform:

- **Frontend:** Static export or Node.js server
- **Backend:** Python ASGI server (Uvicorn/Gunicorn)
- **Workers:** Celery with Redis broker
- **Database:** PostgreSQL with connection pooling

## 📝 License

MIT License - see LICENSE file for details. 