#!/bin/bash

# Fair-Edge Environment Switcher
# Usage: ./switch-env.sh [local|production]

ENV=${1:-local}

case $ENV in
    local|dev)
        echo "🔧 Switching to LOCAL environment..."
        if [ -f .env.local ]; then
            cp .env.local .env
            echo "✅ Now using .env.local"
            echo "📍 API URL: http://localhost:8000"
            echo "⚡ Refresh: Every 5 minutes (stress test)"
        else
            echo "❌ .env.local not found!"
            exit 1
        fi
        ;;
    
    prod|production)
        echo "🚀 Switching to PRODUCTION environment..."
        if [ -f .env.production ]; then
            cp .env.production .env
            echo "✅ Now using .env.production"
            echo "🌐 Domain: https://dock108.ai"
            echo "📊 Refresh: 30 min during business hours"
        else
            echo "❌ .env.production not found!"
            exit 1
        fi
        ;;
    
    *)
        echo "❓ Usage: ./switch-env.sh [local|production]"
        exit 1
        ;;
esac

echo ""
echo "Next steps:"
echo "  - For local: docker compose up -d"
echo "  - For production: ./deploy.sh production"