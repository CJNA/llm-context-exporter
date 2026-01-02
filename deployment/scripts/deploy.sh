#!/bin/bash

# LLM Context Exporter Deployment Script
# This script handles the complete deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$DEPLOYMENT_DIR")"
CONFIG_FILE="$DEPLOYMENT_DIR/config/production.env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking deployment requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if configuration file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        log_info "Please copy production.env.example to production.env and configure it."
        exit 1
    fi
    
    log_success "All requirements met"
}

validate_config() {
    log_info "Validating configuration..."
    
    # Source the config file
    source "$CONFIG_FILE"
    
    # Check required variables
    required_vars=(
        "SECRET_KEY"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "STRIPE_SECRET_KEY"
        "DOMAIN_NAME"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Check if SECRET_KEY is not the default
    if [ "$SECRET_KEY" = "your-super-secret-key-change-this-in-production" ]; then
        log_error "SECRET_KEY is still set to the default value. Please change it."
        exit 1
    fi
    
    log_success "Configuration validated"
}

setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    source "$CONFIG_FILE"
    
    if [ "$ENFORCE_HTTPS" = "true" ]; then
        # Check if certificates already exist
        if [ ! -f "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" ]; then
            log_info "Obtaining SSL certificate for $DOMAIN_NAME..."
            
            # Use certbot to obtain certificate
            docker run --rm \
                -v ssl_certs:/etc/letsencrypt \
                -p 80:80 \
                certbot/certbot certonly \
                --standalone \
                --email "$EMAIL_FOR_SSL" \
                --agree-tos \
                --no-eff-email \
                -d "$DOMAIN_NAME"
            
            if [ $? -eq 0 ]; then
                log_success "SSL certificate obtained successfully"
            else
                log_error "Failed to obtain SSL certificate"
                exit 1
            fi
        else
            log_info "SSL certificate already exists"
        fi
    else
        log_warning "HTTPS is not enforced. Consider enabling it for production."
    fi
}

build_and_deploy() {
    log_info "Building and deploying application..."
    
    cd "$DEPLOYMENT_DIR/docker"
    
    # Pull latest images
    docker-compose -f docker-compose.prod.yml pull
    
    # Build the application
    log_info "Building application image..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check health
    if docker-compose -f docker-compose.prod.yml ps | grep -q "unhealthy"; then
        log_error "Some services are unhealthy"
        docker-compose -f docker-compose.prod.yml ps
        exit 1
    fi
    
    log_success "Application deployed successfully"
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Prometheus and Grafana are already included in docker-compose
    # Just verify they're running
    cd "$DEPLOYMENT_DIR/docker"
    
    if docker-compose -f docker-compose.prod.yml ps prometheus | grep -q "Up"; then
        log_success "Prometheus is running on port 9090"
    else
        log_warning "Prometheus is not running properly"
    fi
    
    if docker-compose -f docker-compose.prod.yml ps grafana | grep -q "Up"; then
        log_success "Grafana is running on port 3000"
    else
        log_warning "Grafana is not running properly"
    fi
}

setup_backups() {
    log_info "Setting up backup system..."
    
    # Create backup directory
    mkdir -p "$DEPLOYMENT_DIR/docker/backups"
    
    # Set up cron job for daily backups
    BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"
    
    # Add to crontab if not already present
    if ! crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
        (crontab -l 2>/dev/null; echo "0 2 * * * $BACKUP_SCRIPT") | crontab -
        log_success "Daily backup cron job added"
    else
        log_info "Backup cron job already exists"
    fi
}

run_health_check() {
    log_info "Running health checks..."
    
    source "$CONFIG_FILE"
    
    # Check main application
    if curl -f "http://localhost/health" > /dev/null 2>&1; then
        log_success "Application health check passed"
    else
        log_error "Application health check failed"
        exit 1
    fi
    
    # Check if HTTPS is working (if enabled)
    if [ "$ENFORCE_HTTPS" = "true" ]; then
        if curl -f "https://$DOMAIN_NAME/health" > /dev/null 2>&1; then
            log_success "HTTPS health check passed"
        else
            log_warning "HTTPS health check failed"
        fi
    fi
}

show_deployment_info() {
    log_info "Deployment completed successfully!"
    echo
    echo "=== Deployment Information ==="
    echo "Application URL: http://localhost"
    echo "Prometheus: http://localhost:9090"
    echo "Grafana: http://localhost:3000"
    echo
    echo "=== Useful Commands ==="
    echo "View logs: docker-compose -f $DEPLOYMENT_DIR/docker/docker-compose.prod.yml logs -f"
    echo "Stop services: docker-compose -f $DEPLOYMENT_DIR/docker/docker-compose.prod.yml down"
    echo "Restart services: docker-compose -f $DEPLOYMENT_DIR/docker/docker-compose.prod.yml restart"
    echo "Run backup: $SCRIPT_DIR/backup.sh"
    echo
    echo "=== Next Steps ==="
    echo "1. Configure your domain DNS to point to this server"
    echo "2. Set up SSL certificate renewal (certbot renew)"
    echo "3. Configure monitoring alerts"
    echo "4. Test the complete application flow"
}

# Main deployment process
main() {
    log_info "Starting LLM Context Exporter deployment..."
    
    check_requirements
    validate_config
    setup_ssl
    build_and_deploy
    setup_monitoring
    setup_backups
    run_health_check
    show_deployment_info
    
    log_success "Deployment completed successfully!"
}

# Handle script arguments
case "${1:-}" in
    "check")
        check_requirements
        validate_config
        ;;
    "ssl")
        setup_ssl
        ;;
    "build")
        build_and_deploy
        ;;
    "health")
        run_health_check
        ;;
    *)
        main
        ;;
esac