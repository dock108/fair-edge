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

# Append frontend-specific VITE_ variables to the main env file
echo "" >> "$PROJECT_ROOT/.env.local"
echo "# Frontend Configuration (VITE_ prefix)" >> "$PROJECT_ROOT/.env.local"
echo "VITE_API_URL=http://localhost:8000" >> "$PROJECT_ROOT/.env.local"
echo "VITE_SUPABASE_URL=https://orefwmdofxdxjjvpmmxr.supabase.co" >> "$PROJECT_ROOT/.env.local"
echo "VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9yZWZ3bWRvZnhkeGpqdnBtbXhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg3OTE0NjYsImV4cCI6MjA2NDM2NzQ2Nn0.h4tvayJUqMNh9J09-dVK-2i3qir8zP0oh7iJEq4bktw" >> "$PROJECT_ROOT/.env.local"

echo "✅ Environment files created:"
echo "  - .env.local (unified backend + frontend with VITE_ prefixes)"

echo ""
echo "🚀 Start development with:"
echo "  docker compose up -d"
echo ""
echo "📝 Edit .env.local with your API keys if needed"
echo "   See .env.example for required variables"