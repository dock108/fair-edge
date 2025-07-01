#!/bin/bash

# Production Environment Setup Script
# This script sets up the production environment with proper configs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Setting up Fair-Edge production environment..."

# Copy environment files
echo "📋 Copying environment configuration..."
cp "$PROJECT_ROOT/environments/production.env" "$PROJECT_ROOT/.env.production"

# Append frontend-specific VITE_ variables to the main env file
echo "" >> "$PROJECT_ROOT/.env.production"
echo "# Frontend Configuration (VITE_ prefix)" >> "$PROJECT_ROOT/.env.production"
echo "VITE_API_URL=https://dock108.ai" >> "$PROJECT_ROOT/.env.production"
echo "VITE_SUPABASE_URL=https://orefwmdofxdxjjvpmmxr.supabase.co" >> "$PROJECT_ROOT/.env.production"
echo "VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9yZWZ3bWRvZnhkeGpqdnBtbXhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg3OTE0NjYsImV4cCI6MjA2NDM2NzQ2Nn0.h4tvayJUqMNh9J09-dVK-2i3qir8zP0oh7iJEq4bktw" >> "$PROJECT_ROOT/.env.production"

# Create frontend .env file for Vite (production)
echo "📋 Creating frontend environment file..."
cat > "$PROJECT_ROOT/frontend/.env" << EOF
VITE_API_URL=https://dock108.ai
VITE_SUPABASE_URL=https://orefwmdofxdxjjvpmmxr.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9yZWZ3bWRvZnhkeGpqdnBtbXhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg3OTE0NjYsImV4cCI6MjA2NDM2NzQ2Nn0.h4tvayJUqMNh9J09-dVK-2i3qir8zP0oh7iJEq4bktw
EOF

echo "✅ Environment files created:"
echo "  - .env.production (unified backend + frontend with VITE_ prefixes)"
echo "  - frontend/.env (Vite environment variables)"

echo ""
echo "🚀 Deploy to production with:"
echo "  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo ""
echo "📝 Edit .env.production with your production API keys if needed"
echo "   Make sure to update domain settings for your environment"