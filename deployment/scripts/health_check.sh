#!/bin/bash

# Health Check Script for LLM Context Exporter
# This script performs comprehensive health checks on all services

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

check_docker_services() {
    log_info "Checking Docker services..."
    
    cd "$DEPLOYMENT_DIR/docker"
    
    local services=("app" "postgres" "redis" "prometheus" "grafana")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.prod.yml ps "$service" | grep -q "Up"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
            all_healthy=false
        fi
    done
    
    return $([ "$all_healthy" = true ])
}

check_application_health() {
    log_info "Checking application health endpoint..."
    
    local health_url="http://localhost/health"
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        log_success "Application health check passed (HTTP $response)"
        return 0
    else
        log_error "Application health check failed (HTTP $response)"
        return 1
    fi
}

check_database_connection() {
    log_info "Checking database connection..."
    
    local db_check=$(docker exec llm-context-postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" 2>/dev/null || echo "failed")
    
    if echo "$db_check" | grep -q "accepting connections"; then
        log_success "Database connection is healthy"
        return 0
    else
        log_error "Database connection failed"
        return 1
    fi
}

check_redis_connection() {
    log_info "Checking Redis connection..."
    
    local redis_check=$(docker exec llm-context-redis redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null || echo "failed")
    
    if [ "$redis_check" = "PONG" ]; then
        log_success "Redis connection is healthy"
        return 0
    else
        log_error "Redis connection failed"
        return 1
    fi
}

check_ssl_certificate() {
    log_info "Checking SSL certificate..."
    
    if [ "$ENFORCE_HTTPS" = "true" ]; then
        local cert_path="/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem"
        
        if docker run --rm -v ssl_certs:/certs alpine:latest test -f "/certs/live/$DOMAIN_NAME/fullchain.pem"; then
            # Check certificate expiration
            local expiry_date=$(docker run --rm -v ssl_certs:/certs alpine:latest \
                openssl x509 -in "/certs/live/$DOMAIN_NAME/fullchain.pem" -noout -enddate | cut -d= -f2)
            
            local expiry_timestamp=$(date -d "$expiry_date" +%s)
            local current_timestamp=$(date +%s)
            local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
            
            if [ $days_until_expiry -gt 30 ]; then
                log_success "SSL certificate is valid (expires in $days_until_expiry days)"
                return 0
            elif [ $days_until_expiry -gt 0 ]; then
                log_warning "SSL certificate expires soon ($days_until_expiry days)"
                return 0
            else
                log_error "SSL certificate has expired"
                return 1
            fi
        else
            log_error "SSL certificate not found"
            return 1
        fi
    else
        log_info "HTTPS not enforced, skipping SSL check"
        return 0
    fi
}

check_disk_space() {
    log_info "Checking disk space..."
    
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -lt 80 ]; then
        log_success "Disk usage is healthy ($disk_usage%)"
        return 0
    elif [ "$disk_usage" -lt 90 ]; then
        log_warning "Disk usage is high ($disk_usage%)"
        return 0
    else
        log_error "Disk usage is critical ($disk_usage%)"
        return 1
    fi
}

check_memory_usage() {
    log_info "Checking memory usage..."
    
    local memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$memory_usage" -lt 80 ]; then
        log_success "Memory usage is healthy ($memory_usage%)"
        return 0
    elif [ "$memory_usage" -lt 90 ]; then
        log_warning "Memory usage is high ($memory_usage%)"
        return 0
    else
        log_error "Memory usage is critical ($memory_usage%)"
        return 1
    fi
}

check_api_endpoints() {
    log_info "Checking API endpoints..."
    
    local base_url="http://localhost"
    local endpoints=("/api/health" "/api/beta/status")
    local all_healthy=true
    
    for endpoint in "${endpoints[@]}"; do
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$base_url$endpoint" 2>/dev/null || echo "000")
        
        if [ "$response" = "200" ] || [ "$response" = "401" ]; then
            log_success "API endpoint $endpoint is responding (HTTP $response)"
        else
            log_error "API endpoint $endpoint failed (HTTP $response)"
            all_healthy=false
        fi
    done
    
    return $([ "$all_healthy" = true ])
}

check_stripe_connectivity() {
    log_info "Checking Stripe connectivity..."
    
    # Test Stripe API connectivity (without making actual requests)
    local stripe_test=$(curl -s -o /dev/null -w "%{http_code}" "https://api.stripe.com/v1" 2>/dev/null || echo "000")
    
    if [ "$stripe_test" = "401" ]; then
        log_success "Stripe API is reachable"
        return 0
    else
        log_warning "Stripe API connectivity issue (HTTP $stripe_test)"
        return 1
    fi
}

check_monitoring_services() {
    log_info "Checking monitoring services..."
    
    # Check Prometheus
    local prometheus_health=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:9090/-/healthy" 2>/dev/null || echo "000")
    if [ "$prometheus_health" = "200" ]; then
        log_success "Prometheus is healthy"
    else
        log_warning "Prometheus health check failed (HTTP $prometheus_health)"
    fi
    
    # Check Grafana
    local grafana_health=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/api/health" 2>/dev/null || echo "000")
    if [ "$grafana_health" = "200" ]; then
        log_success "Grafana is healthy"
    else
        log_warning "Grafana health check failed (HTTP $grafana_health)"
    fi
}

generate_health_report() {
    local timestamp=$(date)
    local report_file="/tmp/health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "LLM Context Exporter Health Report"
        echo "Generated: $timestamp"
        echo "=================================="
        echo
        
        echo "Docker Services:"
        cd "$DEPLOYMENT_DIR/docker"
        docker-compose -f docker-compose.prod.yml ps
        echo
        
        echo "System Resources:"
        echo "Disk Usage: $(df -h / | awk 'NR==2 {print $5}')"
        echo "Memory Usage: $(free -h | awk 'NR==2{printf "%s/%s (%.0f%%)", $3,$2,$3*100/$2}')"
        echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"
        echo
        
        echo "Application Logs (last 50 lines):"
        docker-compose -f docker-compose.prod.yml logs --tail=50 app
        
    } > "$report_file"
    
    echo "$report_file"
}

# Main health check process
main() {
    log_info "Starting comprehensive health check..."
    
    local checks_passed=0
    local total_checks=0
    
    # Run all health checks
    local checks=(
        "check_docker_services"
        "check_application_health"
        "check_database_connection"
        "check_redis_connection"
        "check_ssl_certificate"
        "check_disk_space"
        "check_memory_usage"
        "check_api_endpoints"
        "check_stripe_connectivity"
        "check_monitoring_services"
    )
    
    for check in "${checks[@]}"; do
        total_checks=$((total_checks + 1))
        if $check; then
            checks_passed=$((checks_passed + 1))
        fi
        echo
    done
    
    # Generate summary
    log_info "Health Check Summary:"
    echo "Checks passed: $checks_passed/$total_checks"
    
    if [ $checks_passed -eq $total_checks ]; then
        log_success "All health checks passed!"
        exit 0
    elif [ $checks_passed -gt $((total_checks / 2)) ]; then
        log_warning "Some health checks failed, but system is mostly healthy"
        exit 1
    else
        log_error "Multiple health checks failed, system may be unhealthy"
        
        # Generate detailed report
        local report_file=$(generate_health_report)
        log_info "Detailed health report generated: $report_file"
        
        exit 2
    fi
}

# Handle script arguments
case "${1:-}" in
    "quick")
        check_application_health && check_database_connection && check_redis_connection
        ;;
    "services")
        check_docker_services
        ;;
    "ssl")
        check_ssl_certificate
        ;;
    "api")
        check_api_endpoints
        ;;
    "monitoring")
        check_monitoring_services
        ;;
    "report")
        generate_health_report
        ;;
    *)
        main
        ;;
esac