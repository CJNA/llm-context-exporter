#!/bin/bash

# SSL Certificate Setup Script for LLM Context Exporter
# This script handles SSL certificate generation and renewal

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$SCRIPT_DIR")"
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

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    log_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if domain is configured
    if [ -z "$DOMAIN_NAME" ]; then
        log_error "DOMAIN_NAME is not configured in $CONFIG_FILE"
        exit 1
    fi
    
    # Check if email is configured
    if [ -z "$EMAIL_FOR_SSL" ]; then
        log_error "EMAIL_FOR_SSL is not configured in $CONFIG_FILE"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

verify_dns() {
    log_info "Verifying DNS configuration for $DOMAIN_NAME..."
    
    # Get the public IP of this server
    local server_ip=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "unknown")
    
    # Resolve the domain
    local domain_ip=$(dig +short "$DOMAIN_NAME" | tail -n1)
    
    if [ -z "$domain_ip" ]; then
        log_error "Domain $DOMAIN_NAME does not resolve to any IP"
        return 1
    fi
    
    if [ "$server_ip" = "$domain_ip" ]; then
        log_success "DNS is correctly configured ($DOMAIN_NAME -> $domain_ip)"
        return 0
    else
        log_warning "DNS mismatch: $DOMAIN_NAME resolves to $domain_ip, but server IP is $server_ip"
        log_warning "SSL certificate generation may fail if the domain doesn't point to this server"
        return 1
    fi
}

stop_services() {
    log_info "Stopping services to free port 80..."
    
    cd "$DEPLOYMENT_DIR/docker"
    
    # Stop the application temporarily
    if docker-compose -f docker-compose.prod.yml ps app | grep -q "Up"; then
        docker-compose -f docker-compose.prod.yml stop app
        log_info "Application stopped"
    fi
}

start_services() {
    log_info "Starting services..."
    
    cd "$DEPLOYMENT_DIR/docker"
    
    # Start the application
    docker-compose -f docker-compose.prod.yml up -d app
    log_info "Application started"
}

obtain_certificate() {
    log_info "Obtaining SSL certificate for $DOMAIN_NAME..."
    
    # Create SSL certificates volume if it doesn't exist
    docker volume create ssl_certs >/dev/null 2>&1 || true
    
    # Run certbot to obtain certificate
    docker run --rm \
        -v ssl_certs:/etc/letsencrypt \
        -p 80:80 \
        certbot/certbot certonly \
        --standalone \
        --email "$EMAIL_FOR_SSL" \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        -d "$DOMAIN_NAME"
    
    if [ $? -eq 0 ]; then
        log_success "SSL certificate obtained successfully"
        return 0
    else
        log_error "Failed to obtain SSL certificate"
        return 1
    fi
}

renew_certificate() {
    log_info "Renewing SSL certificate..."
    
    # Stop nginx temporarily
    stop_services
    
    # Renew certificate
    docker run --rm \
        -v ssl_certs:/etc/letsencrypt \
        -p 80:80 \
        certbot/certbot renew \
        --standalone \
        --force-renewal
    
    local renewal_result=$?
    
    # Start services again
    start_services
    
    if [ $renewal_result -eq 0 ]; then
        log_success "SSL certificate renewed successfully"
        
        # Reload nginx to use new certificate
        docker-compose -f "$DEPLOYMENT_DIR/docker/docker-compose.prod.yml" exec app nginx -s reload
        
        return 0
    else
        log_error "Failed to renew SSL certificate"
        return 1
    fi
}

check_certificate() {
    log_info "Checking SSL certificate status..."
    
    # Check if certificate exists
    if docker run --rm -v ssl_certs:/certs alpine:latest test -f "/certs/live/$DOMAIN_NAME/fullchain.pem"; then
        # Get certificate information
        local cert_info=$(docker run --rm -v ssl_certs:/certs alpine:latest \
            openssl x509 -in "/certs/live/$DOMAIN_NAME/fullchain.pem" -noout -dates)
        
        local not_before=$(echo "$cert_info" | grep "notBefore" | cut -d= -f2)
        local not_after=$(echo "$cert_info" | grep "notAfter" | cut -d= -f2)
        
        log_info "Certificate valid from: $not_before"
        log_info "Certificate expires: $not_after"
        
        # Check expiration
        local expiry_timestamp=$(date -d "$not_after" +%s)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [ $days_until_expiry -gt 30 ]; then
            log_success "Certificate is valid for $days_until_expiry more days"
            return 0
        elif [ $days_until_expiry -gt 0 ]; then
            log_warning "Certificate expires in $days_until_expiry days - consider renewal"
            return 1
        else
            log_error "Certificate has expired $((days_until_expiry * -1)) days ago"
            return 2
        fi
    else
        log_error "No certificate found for $DOMAIN_NAME"
        return 3
    fi
}

setup_auto_renewal() {
    log_info "Setting up automatic certificate renewal..."
    
    local renewal_script="$SCRIPT_DIR/ssl_setup.sh"
    local cron_job="0 3 * * 0 $renewal_script renew"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$renewal_script renew"; then
        log_info "Auto-renewal cron job already exists"
    else
        # Add cron job for weekly renewal check
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        log_success "Auto-renewal cron job added (runs weekly on Sunday at 3 AM)"
    fi
}

update_nginx_config() {
    log_info "Updating Nginx configuration for HTTPS..."
    
    local nginx_config="$DEPLOYMENT_DIR/docker/nginx.conf"
    local backup_config="$nginx_config.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Backup current config
    cp "$nginx_config" "$backup_config"
    log_info "Nginx config backed up to $backup_config"
    
    # Update nginx config to enable HTTPS
    sed -i "s/# server {/server {/g" "$nginx_config"
    sed -i "s/# listen 443/listen 443/g" "$nginx_config"
    sed -i "s/# ssl_/ssl_/g" "$nginx_config"
    sed -i "s/# add_header Strict-Transport-Security/add_header Strict-Transport-Security/g" "$nginx_config"
    sed -i "s/your-domain.com/$DOMAIN_NAME/g" "$nginx_config"
    
    # Remove comment markers for HTTPS block
    sed -i '/# server {/,/# }/s/^# //' "$nginx_config"
    
    log_success "Nginx configuration updated for HTTPS"
    
    # Reload nginx
    cd "$DEPLOYMENT_DIR/docker"
    if docker-compose -f docker-compose.prod.yml ps app | grep -q "Up"; then
        docker-compose -f docker-compose.prod.yml exec app nginx -t
        if [ $? -eq 0 ]; then
            docker-compose -f docker-compose.prod.yml exec app nginx -s reload
            log_success "Nginx configuration reloaded"
        else
            log_error "Nginx configuration test failed"
            # Restore backup
            cp "$backup_config" "$nginx_config"
            log_info "Nginx configuration restored from backup"
            return 1
        fi
    fi
}

test_https() {
    log_info "Testing HTTPS configuration..."
    
    local https_url="https://$DOMAIN_NAME/health"
    
    # Wait a moment for nginx to reload
    sleep 5
    
    # Test HTTPS endpoint
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$https_url" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        log_success "HTTPS is working correctly"
        
        # Test SSL certificate
        local ssl_info=$(echo | openssl s_client -servername "$DOMAIN_NAME" -connect "$DOMAIN_NAME:443" 2>/dev/null | openssl x509 -noout -subject)
        log_info "SSL Certificate: $ssl_info"
        
        return 0
    else
        log_error "HTTPS test failed (HTTP $response)"
        return 1
    fi
}

# Main SSL setup process
main() {
    log_info "Starting SSL setup for $DOMAIN_NAME..."
    
    check_prerequisites
    
    # Check current certificate status
    check_certificate
    local cert_status=$?
    
    if [ $cert_status -eq 0 ]; then
        log_info "Valid certificate already exists"
    else
        # Verify DNS before attempting certificate generation
        if ! verify_dns; then
            log_error "DNS verification failed. Please ensure $DOMAIN_NAME points to this server."
            exit 1
        fi
        
        # Stop services and obtain certificate
        stop_services
        
        if obtain_certificate; then
            start_services
            update_nginx_config
            test_https
        else
            start_services
            exit 1
        fi
    fi
    
    # Set up auto-renewal
    setup_auto_renewal
    
    log_success "SSL setup completed successfully!"
    log_info "Your site is now available at: https://$DOMAIN_NAME"
}

# Handle script arguments
case "${1:-}" in
    "check")
        check_certificate
        ;;
    "renew")
        renew_certificate
        ;;
    "obtain")
        check_prerequisites
        verify_dns
        stop_services
        obtain_certificate
        start_services
        ;;
    "test")
        test_https
        ;;
    "auto-renew")
        setup_auto_renewal
        ;;
    *)
        main
        ;;
esac