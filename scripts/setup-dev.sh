#!/bin/bash

# Development Environment Setup Script
# This script sets up the development environment with proper configs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔧 Setting up Fair-Edge development environment..."

# Copy environment files
echo "📋 Copying environment configuration..."
cp "$PROJECT_ROOT/environments/development.env" "$PROJECT_ROOT/.env.local"
cp "$PROJECT_ROOT/environments/frontend.development.env" "$PROJECT_ROOT/frontend/.env.local"

echo "✅ Environment files created:"
echo "  - .env.local (backend)"
echo "  - frontend/.env.local (frontend)"

echo ""
echo "🚀 Start development with:"
echo "  docker compose up -d"
echo ""
echo "📝 Edit .env.local and frontend/.env.local with your API keys"
echo "   See .env.example for required variables"