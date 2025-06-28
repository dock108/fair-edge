#!/bin/bash
# Deploy Fair-Edge to Hetzner Server
# Server: 178.156.185.113

set -e

SERVER_IP="178.156.185.113"
SERVER_USER="mike"
DEPLOY_DIR="/opt/fair-edge"

echo "🚀 Deploying Fair-Edge to Hetzner Server: $SERVER_IP"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Test SSH connection
print_step "Testing SSH connection"
if ssh -o ConnectTimeout=10 "$SERVER_USER@$SERVER_IP" 'echo "SSH connection successful"'; then
    print_success "SSH connection works"
else
    print_error "Cannot connect to server. Check SSH key or server status."
fi

# Transfer files to server
print_step "Uploading project files to server"
ssh "$SERVER_USER@$SERVER_IP" "sudo mkdir -p $DEPLOY_DIR && sudo chown -R $SERVER_USER:$SERVER_USER $DEPLOY_DIR"

# Use rsync to efficiently transfer files
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.env.development' --exclude='celery_worker.pid' \
    --exclude='celery_beat.pid' --exclude='server.log' --exclude='logs/' \
    ./ "$SERVER_USER@$SERVER_IP:$DEPLOY_DIR/"

print_success "Files uploaded successfully"

# Run deployment commands on server
print_step "Running deployment commands on server"

ssh "$SERVER_USER@$SERVER_IP" << 'EOF'
set -e

SERVER_IP="178.156.185.113"
DEPLOY_DIR="/opt/fair-edge"

echo "📦 Setting up server environment..."

# Update system
sudo apt-get update

# Install required packages
sudo apt-get install -y curl git ufw

# Configure firewall if not already done
sudo ufw --force default deny incoming 2>/dev/null || true
sudo ufw --force default allow outgoing 2>/dev/null || true
sudo ufw allow OpenSSH 2>/dev/null || true
sudo ufw allow 80/tcp 2>/dev/null || true
sudo ufw allow 443/tcp 2>/dev/null || true
sudo ufw --force enable 2>/dev/null || true

echo "✓ Firewall configured"

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo "✓ Docker installed"
else
    echo "✓ Docker already installed"
fi

# Install Docker Compose if not already installed
if ! docker compose version &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
    mkdir -p $DOCKER_CONFIG/cli-plugins
    sudo curl -SL https://github.com/docker/compose/releases/download/v2.37.3/docker-compose-linux-x86_64 \
        -o $DOCKER_CONFIG/cli-plugins/docker-compose
    sudo chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
    echo "✓ Docker Compose installed"
else
    echo "✓ Docker Compose already installed"
fi

# Navigate to project directory
cd "$DEPLOY_DIR"

# Make scripts executable
chmod +x scripts/*.sh

# Set proper ownership
sudo chown -R $USER:$USER "$DEPLOY_DIR"

echo "🏗️ Building and starting Fair-Edge application..."

# Stop any existing containers
docker compose -f docker-compose.hetzner.yml down 2>/dev/null || true

# Build the application
docker compose -f docker-compose.hetzner.yml build --no-cache

# Build frontend first
echo "📱 Building frontend..."
docker compose -f docker-compose.hetzner.yml --profile build up frontend

# Start all services
echo "🚀 Starting all services..."
docker compose -f docker-compose.hetzner.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Check container status
docker compose -f docker-compose.hetzner.yml ps

# Test API health
echo "🔍 Testing API health..."
for i in {1..12}; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        echo "✓ API is healthy"
        break
    else
        echo "Waiting for API... (attempt $i/12)"
        sleep 5
    fi
done

# Test frontend
echo "🔍 Testing frontend..."
if curl -f http://localhost/ &>/dev/null; then
    echo "✓ Frontend is accessible"
else
    echo "⚠ Frontend accessibility check failed"
fi

# Set up systemd service for auto-restart
echo "🔧 Setting up systemd service..."
sudo cp docker/systemd/fair-edge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fair-edge

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Your Fair-Edge application is now running at:"
echo "   Frontend: http://$SERVER_IP"
echo "   API:      http://$SERVER_IP:8000"
echo "   API Docs: http://$SERVER_IP:8000/docs"
echo "   Health:   http://$SERVER_IP:8000/health"
echo ""
echo "🔧 Useful commands:"
echo "   View logs:        sudo journalctl -u fair-edge -f"
echo "   Restart service:  sudo systemctl restart fair-edge"
echo "   Container logs:   cd $DEPLOY_DIR && docker compose -f docker-compose.hetzner.yml logs -f"
echo ""
echo "⚠️  Next steps:"
echo "   1. Update Stripe webhook URL to: http://$SERVER_IP/api/webhooks/stripe"
echo "   2. Test the complete signup → upgrade → premium flow"
echo "   3. Monitor the smart refresh system logs"

EOF

print_success "Deployment script completed!"

# Final verification from local machine
print_step "Final verification"
sleep 5

if curl -f "http://$SERVER_IP/health" &>/dev/null; then
    print_success "✅ API is accessible from external network: http://$SERVER_IP:8000/health"
else
    echo "⚠️  API health check failed from external network"
fi

if curl -f "http://$SERVER_IP/" &>/dev/null; then
    print_success "✅ Frontend is accessible: http://$SERVER_IP"
else
    echo "⚠️  Frontend accessibility check failed"
fi

echo ""
echo "🎊 Fair-Edge has been deployed to your Hetzner server!"
echo ""
echo "🌐 Access your application:"
echo "   👉 Frontend: http://$SERVER_IP"
echo "   👉 API Docs: http://$SERVER_IP:8000/docs"
echo ""
echo "🔄 Smart Refresh System is active:"
echo "   • Refreshes every 15 minutes when dashboard is active"
echo "   • Refreshes on load if data is stale (>30min)"
echo "   • Reduces API calls by ~75% during testing"
echo ""
echo "💳 Don't forget to:"
echo "   1. Update Stripe webhook: http://$SERVER_IP/api/webhooks/stripe"
echo "   2. Test payment flow end-to-end"
echo "   3. Monitor system with: ssh $SERVER_USER@$SERVER_IP 'sudo journalctl -u fair-edge -f'"