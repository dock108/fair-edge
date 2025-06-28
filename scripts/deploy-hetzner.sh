#!/bin/bash
# FairEdge Hetzner Production Deployment Script
# This script automates the deployment of FairEdge on a fresh Hetzner VPS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="/opt/fair-edge"
SERVICE_NAME="fair-edge"

# Functions
print_step() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root. Use: sudo $0"
    fi
}

check_requirements() {
    print_step "Checking requirements"
    
    # Check if we're on a Hetzner VPS (optional check)
    if command -v dmidecode &> /dev/null; then
        if dmidecode -s system-manufacturer 2>/dev/null | grep -q "Hetzner"; then
            print_success "Running on Hetzner infrastructure"
        else
            print_warning "Not detected as Hetzner VPS, but continuing anyway"
        fi
    fi
    
    # Check Ubuntu version
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        if [[ "$ID" == "ubuntu" && "$VERSION_ID" == "22.04" ]]; then
            print_success "Ubuntu 22.04 detected"
        else
            print_warning "Expected Ubuntu 22.04, found $ID $VERSION_ID"
        fi
    fi
}

setup_firewall() {
    print_step "Setting up UFW firewall"
    
    apt-get update
    apt-get install -y ufw
    
    # Default policies
    ufw --force default deny incoming
    ufw --force default allow outgoing
    
    # Allow SSH (be careful not to lock yourself out!)
    ufw allow OpenSSH
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Enable firewall
    ufw --force enable
    
    print_success "Firewall configured"
}

install_docker() {
    print_step "Installing Docker Engine and Compose"
    
    # Install Docker using official script
    curl -fsSL https://get.docker.com | sh
    
    # Install Docker Compose v2 plugin
    DOCKER_CONFIG=${DOCKER_CONFIG:-/root/.docker}
    mkdir -p $DOCKER_CONFIG/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.37.3/docker-compose-linux-x86_64 \
        -o $DOCKER_CONFIG/cli-plugins/docker-compose
    chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
    
    # Verify installation
    docker --version
    docker compose version
    
    print_success "Docker installed successfully"
}

setup_project() {
    print_step "Setting up project directory"
    
    # Create deployment directory
    mkdir -p "$DEPLOY_DIR"
    
    # If we're running from within the project, copy files
    if [[ "$(basename "$PROJECT_DIR")" == "fair-edge" ]]; then
        print_success "Copying project files from current directory"
        cp -r "$PROJECT_DIR"/* "$DEPLOY_DIR"/
        cp -r "$PROJECT_DIR"/.env.* "$DEPLOY_DIR"/ 2>/dev/null || true
        cp -r "$PROJECT_DIR"/.git* "$DEPLOY_DIR"/ 2>/dev/null || true
    else
        print_step "Cloning repository"
        # Change this to your actual repository URL
        git clone https://github.com/your-org/fair-edge.git "$DEPLOY_DIR"
    fi
    
    # Set proper ownership
    chown -R root:root "$DEPLOY_DIR"
    chmod +x "$DEPLOY_DIR"/scripts/*.sh
    
    print_success "Project directory set up"
}

setup_environment() {
    print_step "Setting up environment configuration"
    
    cd "$DEPLOY_DIR"
    
    # Check if .env.production exists
    if [[ ! -f .env.production ]]; then
        if [[ -f .env.hetzner.template ]]; then
            cp .env.hetzner.template .env.production
            print_warning "Created .env.production from template. YOU MUST EDIT IT with real values!"
            print_warning "Edit file: $DEPLOY_DIR/.env.production"
            print_warning "Replace all CHANGE_ME values before proceeding"
            
            read -p "Press Enter after you've edited .env.production with real values..."
        else
            print_error ".env.hetzner.template not found. Cannot create environment file."
        fi
    else
        print_success "Using existing .env.production"
    fi
    
    # Validate that environment file has been edited
    if grep -q "CHANGE_ME" .env.production; then
        print_error "Environment file still contains CHANGE_ME values. Please edit .env.production first."
    fi
    
    print_success "Environment configuration ready"
}

setup_systemd() {
    print_step "Setting up systemd service"
    
    # Copy systemd service file
    cp "$DEPLOY_DIR/docker/systemd/fair-edge.service" /etc/systemd/system/
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service for auto-start
    systemctl enable "$SERVICE_NAME"
    
    print_success "Systemd service configured"
}

deploy_application() {
    print_step "Deploying Fair-Edge application"
    
    cd "$DEPLOY_DIR"
    
    # Pull/build images
    docker compose -f docker-compose.hetzner.yml build --no-cache
    docker compose -f docker-compose.hetzner.yml pull
    
    # Build frontend
    docker compose -f docker-compose.hetzner.yml --profile build up frontend
    
    # Start the application
    docker compose -f docker-compose.hetzner.yml up -d
    
    print_success "Application deployed"
}

verify_deployment() {
    print_step "Verifying deployment"
    
    # Wait for services to start
    sleep 30
    
    # Check if containers are running
    cd "$DEPLOY_DIR"
    if docker compose -f docker-compose.hetzner.yml ps | grep -q "Up"; then
        print_success "Containers are running"
    else
        print_error "Some containers failed to start"
    fi
    
    # Check health endpoints
    max_attempts=12
    attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            print_success "API health check passed"
            break
        else
            print_warning "API health check failed (attempt $attempt/$max_attempts)"
            sleep 5
            ((attempt++))
        fi
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        print_error "API health check failed after $max_attempts attempts"
    fi
    
    # Check if Caddy is responding
    if curl -f http://localhost/ &>/dev/null; then
        print_success "Frontend is accessible"
    else
        print_warning "Frontend accessibility check failed"
    fi
}

show_completion_info() {
    print_step "Deployment Complete!"
    
    echo -e "\n${GREEN}Fair-Edge has been successfully deployed!${NC}\n"
    
    echo "📋 Next Steps:"
    echo "1. Update your DNS A record to point to this server's IP"
    echo "2. Wait for DNS propagation (5-15 minutes)"
    echo "3. Caddy will automatically obtain SSL certificates"
    echo "4. Test your application at your domain"
    echo ""
    
    echo "🔧 Useful Commands:"
    echo "  View logs:           journalctl -u fair-edge -f"
    echo "  Restart service:     systemctl restart fair-edge"
    echo "  Check status:        systemctl status fair-edge"
    echo "  Docker logs:         cd $DEPLOY_DIR && docker compose -f docker-compose.hetzner.yml logs -f"
    echo ""
    
    echo "📂 Important Files:"
    echo "  Project directory:   $DEPLOY_DIR"
    echo "  Environment config:  $DEPLOY_DIR/.env.production"
    echo "  Service file:        /etc/systemd/system/fair-edge.service"
    echo ""
    
    echo "🔍 Health Checks:"
    echo "  API Health:          http://$(hostname -I | awk '{print $1}'):8000/health"
    echo "  API Docs:            http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo "  Frontend:            http://$(hostname -I | awk '{print $1}')/"
    echo ""
    
    echo "⚠️  Security Reminders:"
    echo "  - Change default SSH port if desired"
    echo "  - Set up SSH key authentication"
    echo "  - Configure automatic security updates"
    echo "  - Set up monitoring and backups"
    echo ""
}

# Main execution
main() {
    print_step "Fair-Edge Hetzner Deployment Starting"
    
    check_root
    check_requirements
    setup_firewall
    install_docker
    setup_project
    setup_environment
    setup_systemd
    deploy_application
    verify_deployment
    show_completion_info
    
    print_success "Deployment script completed successfully!"
}

# Run main function
main "$@"