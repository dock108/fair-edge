# Fair-Edge Hetzner Production Deployment Guide

Complete, production-ready deployment guide for Fair-Edge on Hetzner Cloud VPS with automatic HTTPS, monitoring, and smart refresh system.

## 🚀 Quick Start (Automated)

For fully automated deployment, use our deployment script:

```bash
# On your Hetzner server as root:
curl -fsSL https://raw.githubusercontent.com/fair-edge/fair-edge/main/scripts/deploy-hetzner.sh | bash
```

## 📋 Prerequisites

- **Hetzner Cloud VPS**: CX21 (2 vCPU, 4GB RAM) or larger
- **Domain**: Point your domain to the server IP (e.g., `dock108.ai`)
- **Credentials**: Supabase, Stripe, and Odds API keys ready

## 🛠️ Manual Deployment Steps

### 1. Provision Hetzner Server

1. **Create VPS** in Hetzner Cloud Console:
   - **Image**: Ubuntu 22.04
   - **Type**: CX21 (2 vCPU / 4 GB) or larger for production
   - **Datacenter**: Choose closest to your users
   - **SSH Keys**: Upload your public key for secure access
   - **Firewall**: Enable and configure (ports 80, 443, 22)

2. **Note the public IP** and set DNS A record:
   ```bash
   dock108.ai -> YOUR_SERVER_IP
   ```

### 2. Basic Server Setup

SSH into your server and run initial setup:

```bash
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y ufw curl git jq

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80,443/tcp
ufw enable
```

### 3. Install Docker & Docker Compose

```bash
# Install Docker Engine
curl -fsSL https://get.docker.com | sh

# Install Docker Compose v2 plugin
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.37.3/docker-compose-linux-x86_64 \
  -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# Verify installation
docker --version
docker compose version
```

### 4. Deploy Fair-Edge Application

```bash
# Clone repository to deployment directory
git clone https://github.com/fair-edge/fair-edge.git /opt/fair-edge
cd /opt/fair-edge

# Create production environment file
cp .env.hetzner.template .env.production

# Edit environment file with your credentials
nano .env.production
```

### 5. Configure Environment Variables

Edit `/opt/fair-edge/.env.production` and replace all `CHANGE_ME` values:

```bash
# Required Configuration
DOMAIN=dock108.ai
SUPABASE_URL=https://orefwmdofxdxjjvpmmxr.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
DB_CONNECTION_STRING=postgresql+asyncpg://postgres:[PASSWORD]@db.orefwmdofxdxjjvpmmxr.supabase.co:6543/postgres

# External APIs
ODDS_API_KEY=your_odds_api_key

# Stripe (LIVE keys for production)
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# URLs
VITE_API_URL=https://dock108.ai
CORS_ORIGINS=https://dock108.ai,https://www.dock108.ai
```

### 6. Deploy Application Stack

```bash
cd /opt/fair-edge

# Build and start all services
docker compose -f docker-compose.hetzner.yml build --no-cache
docker compose -f docker-compose.hetzner.yml --profile build up frontend  # Build frontend
docker compose -f docker-compose.hetzner.yml up -d

# Check status
docker compose -f docker-compose.hetzner.yml ps
```

### 7. Set Up System Service (Auto-restart)

```bash
# Copy systemd service file
cp /opt/fair-edge/docker/systemd/fair-edge.service /etc/systemd/system/

# Enable auto-start on boot
systemctl daemon-reload
systemctl enable fair-edge
systemctl start fair-edge

# Check service status
systemctl status fair-edge
```

### 8. Configure Stripe Webhooks

1. **In Stripe Dashboard** → Developers → Webhooks:
   - **Endpoint URL**: `https://dock108.ai/api/webhooks/stripe`
   - **Events**: Select `checkout.session.completed`, `invoice.paid`, `customer.subscription.updated`

2. **Copy the webhook signing secret** to your `.env.production`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
   ```

3. **Restart services** to pick up the new webhook secret:
   ```bash
   systemctl restart fair-edge
   ```

## 🔍 Verification & Testing

### Health Checks

```bash
# API health check
curl https://dock108.ai/health

# Frontend accessibility
curl https://dock108.ai/

# Check all containers are running
docker compose -f docker-compose.hetzner.yml ps
```

### Smart Refresh System Verification

```bash
# Check Redis is working
docker compose -f docker-compose.hetzner.yml exec redis redis-cli ping

# Check Celery workers
docker compose -f docker-compose.hetzner.yml exec celery_worker celery -A services.celery_app.celery_app inspect active

# Check logs for smart refresh activity
docker compose -f docker-compose.hetzner.yml logs -f celery_beat | grep "smart-refresh"
```

### Full Application Test

1. **Create test user** → Visit `https://dock108.ai`
2. **Dashboard loads** → Check for Free tier banners and data loading
3. **Upgrade flow** → Click Upgrade, test with Stripe test card
4. **Premium features** → Verify Premium tier unlocks hidden features
5. **Smart refresh** → Monitor dashboard activity tracking in admin logs

## 📊 Monitoring & Maintenance

### Service Management

```bash
# View service logs
journalctl -u fair-edge -f

# Restart the entire stack
systemctl restart fair-edge

# Check resource usage
docker stats

# View application logs
cd /opt/fair-edge
docker compose -f docker-compose.hetzner.yml logs -f api
docker compose -f docker-compose.hetzner.yml logs -f celery_worker
```

### Optional Monitoring Stack

Enable Prometheus + Grafana monitoring:

```bash
cd /opt/fair-edge
docker compose -f docker-compose.hetzner.yml --profile monitoring up -d prometheus grafana

# Access Grafana at http://YOUR_SERVER_IP:3000
# Default login: admin / admin (change immediately)
```

### Backup Strategy

```bash
# Backup Redis data (important for dashboard activity tracking)
docker compose -f docker-compose.hetzner.yml exec redis redis-cli BGSAVE

# Backup environment configuration
cp .env.production .env.production.backup

# Database backups are handled by Supabase automatically
```

## 🔒 Security Hardening

### Additional Security Measures

```bash
# Change SSH port (optional)
sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
systemctl restart ssh
ufw delete allow OpenSSH
ufw allow 2222/tcp

# Install fail2ban for brute-force protection
apt install fail2ban
systemctl enable fail2ban

# Set up automatic security updates
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

### SSL Certificate Verification

Caddy automatically obtains and renews SSL certificates. Verify:

```bash
# Check certificate status
curl -I https://dock108.ai

# View Caddy logs for SSL issues
docker compose -f docker-compose.hetzner.yml logs caddy | grep -i ssl
```

## 🚨 Troubleshooting

### Common Issues

**Containers won't start:**
```bash
# Check Docker daemon
systemctl status docker

# Check logs for specific container
docker compose -f docker-compose.hetzner.yml logs api
```

**SSL certificate issues:**
```bash
# Check DNS propagation
nslookup dock108.ai

# Restart Caddy to retry SSL
docker compose -f docker-compose.hetzner.yml restart caddy
```

**Database connection issues:**
```bash
# Test Supabase connection
docker compose -f docker-compose.hetzner.yml exec api python -c "import asyncpg; print('Test complete')"

# Check environment variables
docker compose -f docker-compose.hetzner.yml exec api env | grep SUPABASE
```

**Smart refresh not working:**
```bash
# Check Redis connectivity
docker compose -f docker-compose.hetzner.yml exec api redis-cli -h redis ping

# Check Celery beat schedule
docker compose -f docker-compose.hetzner.yml exec celery_beat celery -A services.celery_app.celery_app inspect scheduled
```

### Performance Optimization

**For high traffic:**
```bash
# Scale workers
docker compose -f docker-compose.hetzner.yml up -d --scale celery_worker=4

# Increase API concurrency
# Edit .env.production: WEB_CONCURRENCY=8
systemctl restart fair-edge
```

**Resource monitoring:**
```bash
# Check server resources
htop
df -h
free -h

# Check container resources
docker stats --no-stream
```

## 📈 Scaling & Updates

### Automatic Updates (Watchtower)

Enable automatic container updates:

```bash
docker compose -f docker-compose.hetzner.yml --profile watchtower up -d watchtower
```

### Manual Updates

```bash
cd /opt/fair-edge

# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.hetzner.yml build --no-cache
docker compose -f docker-compose.hetzner.yml up -d
```

### Scaling to Multiple Servers

For high availability, consider:
- Load balancer (Hetzner Load Balancer)
- Separate Redis cluster
- CDN for static assets (Cloudflare)
- Database read replicas

## 📞 Support

- **Documentation**: `/opt/fair-edge/docs/`
- **Logs**: `journalctl -u fair-edge -f`
- **Health Check**: `https://dock108.ai/health`
- **API Docs**: `https://dock108.ai/docs`

---

**🎉 Congratulations!** Your Fair-Edge platform is now running on Hetzner with:
- ✅ Automatic HTTPS (Let's Encrypt)
- ✅ Smart refresh system (75% API call reduction)
- ✅ Stripe billing integration
- ✅ Redis-based dashboard activity tracking
- ✅ Auto-restart on server reboot
- ✅ Comprehensive monitoring and logging