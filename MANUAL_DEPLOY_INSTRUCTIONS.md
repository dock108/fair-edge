# 🚀 Manual Deployment Instructions for Hetzner Server

**Server**: `178.156.185.113`  
**User**: `mike@laptop`

Since we need to set up SSH access first, please follow these steps manually:

## Step 1: Set Up SSH Access

1. **SSH into your server** using the Hetzner Cloud Console or your existing method
2. **Add your SSH public key** to the server:

```bash
# On the server, create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add your public key to authorized_keys
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOtWkN23HyoFQf6KgPW7xQ4LrnM4I7cTmrQlyIrfodN7 mike@laptop" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## Step 2: Test SSH Connection

From your local machine, test the connection:

```bash
ssh mike@178.156.185.113
```

## Step 3: Upload Project Files

Once SSH works, upload the project files:

```bash
# From your local machine, in the fair-edge directory:
cd /Users/michaelfuscoletti/Desktop/fair-edge

# Create deployment directory on server
ssh mike@178.156.185.113 "sudo mkdir -p /opt/fair-edge && sudo chown -R mike:mike /opt/fair-edge"

# Upload files using rsync
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.env.development' --exclude='celery_worker.pid' \
    --exclude='celery_beat.pid' --exclude='server.log' --exclude='logs/' \
    ./ mike@178.156.185.113:/opt/fair-edge/
```

## Step 4: Deploy on Server

SSH into the server and run these commands:

```bash
ssh mike@178.156.185.113

# Navigate to project directory
cd /opt/fair-edge

# Update system
sudo apt-get update

# Install required packages
sudo apt-get install -y curl git ufw

# Configure firewall
sudo ufw --force default deny incoming
sudo ufw --force default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install Docker Compose
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
sudo curl -SL https://github.com/docker/compose/releases/download/v2.37.3/docker-compose-linux-x86_64 \
    -o $DOCKER_CONFIG/cli-plugins/docker-compose
sudo chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# Log out and back in to refresh Docker group membership
exit
```

## Step 5: Build and Deploy Application

SSH back in and deploy:

```bash
ssh mike@178.156.185.113
cd /opt/fair-edge

# Make scripts executable
chmod +x scripts/*.sh

# Build the application
docker compose -f docker-compose.hetzner.yml build --no-cache

# Build frontend
docker compose -f docker-compose.hetzner.yml --profile build up frontend

# Start all services
docker compose -f docker-compose.hetzner.yml up -d

# Check status
docker compose -f docker-compose.hetzner.yml ps
```

## Step 6: Set Up Auto-Restart Service

```bash
# Still on the server
sudo cp docker/systemd/fair-edge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fair-edge
sudo systemctl status fair-edge
```

## Step 7: Verification

Test that everything is working:

```bash
# On the server
curl http://localhost:8000/health
curl http://localhost/

# From your local machine
curl http://178.156.185.113:8000/health
curl http://178.156.185.113/
```

## 🎯 Expected Results

After successful deployment, you should have:

- ✅ **Frontend**: http://178.156.185.113
- ✅ **API**: http://178.156.185.113:8000
- ✅ **API Docs**: http://178.156.185.113:8000/docs
- ✅ **Health Check**: http://178.156.185.113:8000/health

## 🔄 Smart Refresh System

Your smart refresh system is configured with:
- **15-minute auto-refresh** when dashboard is active
- **On-demand refresh** when data is stale (>30min)
- **75% API call reduction** during testing
- **Redis-based activity tracking**

## 📊 Monitoring Commands

```bash
# View application logs
sudo journalctl -u fair-edge -f

# View Docker container logs
cd /opt/fair-edge
docker compose -f docker-compose.hetzner.yml logs -f

# Check container status
docker compose -f docker-compose.hetzner.yml ps

# Check Redis activity
docker compose -f docker-compose.hetzner.yml exec redis redis-cli ping

# Check Celery workers
docker compose -f docker-compose.hetzner.yml exec celery_worker celery -A services.celery_app.celery_app inspect active
```

## 🔧 Troubleshooting

If containers fail to start:
```bash
# Check logs for specific container
docker compose -f docker-compose.hetzner.yml logs api
docker compose -f docker-compose.hetzner.yml logs celery_worker
docker compose -f docker-compose.hetzner.yml logs redis

# Restart everything
docker compose -f docker-compose.hetzner.yml down
docker compose -f docker-compose.hetzner.yml up -d
```

## 💳 Stripe Configuration

Don't forget to update your Stripe webhook URL to:
```
http://178.156.185.113/api/webhooks/stripe
```

---

**Once you've completed these steps, let me know and I can help you test the deployment!** 🚀