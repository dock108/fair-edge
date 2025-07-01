#!/bin/bash

# Production Environment Setup Script
# This script sets up the production environment with proper configs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Setting up Fair-Edge production environment..."

# Copy environment files
echo "📋 Copying environment configuration..."
cp "$PROJECT_ROOT/environments/production.env" "$PROJECT_ROOT/.env.production.local"
cp "$PROJECT_ROOT/environments/frontend.production.env" "$PROJECT_ROOT/frontend/.env.production.local"

echo "✅ Environment files created:"
echo "  - .env.production.local (backend)"
echo "  - frontend/.env.production.local (frontend)"

echo ""
echo "🚀 Deploy to production with:"
echo "  docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d"
echo ""
echo "📝 Edit .env.production.local and frontend/.env.production.local with your production API keys"
echo "   Make sure to update domain settings for your environment"