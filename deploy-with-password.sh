#\!/bin/bash
set -e

SERVER_IP="178.156.185.113"
SERVER_USER="root"
SERVER_PASS="prExtJwAWdUTEFKmEiNH"
DEPLOY_DIR="/opt/fair-edge"

echo "🚀 Deploying Fair-Edge to Hetzner Server: $SERVER_IP"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Upload files
print_step "Uploading project files"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "mkdir -p $DEPLOY_DIR"
sshpass -p "$SERVER_PASS" rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.env.development' --exclude='celery_worker.pid' \
    --exclude='deploy-with-password.sh' \
    -e "sshpass -p $SERVER_PASS ssh -o StrictHostKeyChecking=no" \
    ./ "$SERVER_USER@$SERVER_IP:$DEPLOY_DIR/"
print_success "Files uploaded"

# Run deployment on server
print_step "Setting up server"
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'REMOTE_EOF'
set -e
cd /opt/fair-edge

echo "📦 Installing dependencies..."
apt-get update
apt-get install -y curl git ufw

echo "🔒 Configuring firewall..."
ufw --force default deny incoming
ufw --force default allow outgoing  
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "🐳 Installing Docker..."
if \! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
fi

echo "🔧 Installing Docker Compose..."
if \! docker compose version &> /dev/null; then
    DOCKER_CONFIG=/root/.docker
    mkdir -p $DOCKER_CONFIG/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.37.3/docker-compose-linux-x86_64 \
        -o $DOCKER_CONFIG/cli-plugins/docker-compose
    chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
fi

echo "🏗️ Building application..."
chmod +x scripts/*.sh

# Stop any existing containers
docker compose -f docker-compose.hetzner.yml down 2>/dev/null || true

# Build application
docker compose -f docker-compose.hetzner.yml build --no-cache

# Build frontend
echo "📱 Building frontend..."
docker compose -f docker-compose.hetzner.yml --profile build up frontend

# Start services
echo "🚀 Starting services..."
docker compose -f docker-compose.hetzner.yml up -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "🔍 Checking service status..."
docker compose -f docker-compose.hetzner.yml ps

# Test health
for i in {1..12}; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        echo "✓ API is healthy"
        break
    else
        echo "Waiting for API... (attempt $i/12)"
        sleep 5
    fi
done

# Set up systemd service
echo "🔧 Setting up auto-restart service..."
cp docker/systemd/fair-edge.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable fair-edge

echo "🎉 Deployment complete\!"
echo "Frontend: http://178.156.185.113"
echo "API: http://178.156.185.113:8000"
echo "Health: http://178.156.185.113:8000/health"
REMOTE_EOF

print_success "Server setup complete"

# Final verification
print_step "Final verification"
sleep 5
if curl -f "http://$SERVER_IP:8000/health" &>/dev/null; then
    print_success "✅ API accessible: http://$SERVER_IP:8000"
else
    echo "⚠️ API not yet accessible"
fi

if curl -f "http://$SERVER_IP/" &>/dev/null; then
    print_success "✅ Frontend accessible: http://$SERVER_IP"
else
    echo "⚠️ Frontend not yet accessible" 
fi

echo ""
echo "🎊 Fair-Edge deployed successfully\!"
echo "🌐 Access your application at: http://$SERVER_IP"
echo "📚 API Documentation: http://$SERVER_IP:8000/docs"
echo "🔄 Smart refresh system is active (15min intervals when dashboard active)"
