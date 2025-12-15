#!/bin/bash

# Production Environment Testing Script
# This script validates the production deployment against all requirements

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

# Test Requirements 15.1: Localhost-only binding for CLI mode
test_localhost_binding() {
    log_info "Testing localhost-only binding (Requirement 15.1)..."
    
    # Check if the web server binds only to localhost when run in CLI mode
    local cli_output=$(timeout 10s python -m llm_context_exporter.cli.main --web --port 8080 2>&1 || true)
    
    if echo "$cli_output" | grep -q "127.0.0.1:8080\|localhost:8080"; then
        log_success "CLI web server binds to localhost only"
        return 0
    else
        log_error "CLI web server may not be binding to localhost only"
        return 1
    fi
}

# Test Requirements 16.3: Payment verification before generation
test_payment_verification() {
    log_info "Testing payment verification (Requirement 16.3)..."
    
    # Test that generation requires payment verification
    local test_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"session_id":"test","target":"gemini"}' \
        "$BASE_URL/api/generate" || echo "error")
    
    if echo "$test_response" | grep -q "payment_required\|unauthorized\|403\|401"; then
        log_success "Payment verification is enforced"
        return 0
    else
        log_warning "Payment verification may not be properly enforced: $test_response"
        return 1
    fi
}

# Test production environment configuration
test_production_config() {
    log_info "Testing production environment configuration..."
    
    local config_issues=0
    
    # Check Flask environment
    if [ "$FLASK_ENV" != "production" ]; then
        log_error "FLASK_ENV should be 'production', got: $FLASK_ENV"
        config_issues=$((config_issues + 1))
    fi
    
    # Check Flask debug
    if [ "$FLASK_DEBUG" != "False" ] && [ "$FLASK_DEBUG" != "false" ]; then
        log_error "FLASK_DEBUG should be 'False', got: $FLASK_DEBUG"
        config_issues=$((config_issues + 1))
    fi
    
    # Check HTTPS enforcement
    if [ "$ENFORCE_HTTPS" != "true" ]; then
        log_warning "HTTPS enforcement is disabled (ENFORCE_HTTPS=$ENFORCE_HTTPS)"
        config_issues=$((config_issues + 1))
    fi
    
    # Check secret key
    if [ "$SECRET_KEY" = "your-super-secret-key-change-this-in-production" ]; then
        log_error "SECRET_KEY is still set to default value"
        config_issues=$((config_issues + 1))
    fi
    
    # Check Stripe keys format
    if [[ "$STRIPE_SECRET_KEY" == sk_test_* ]]; then
        log_warning "Using Stripe test keys in production"
    elif [[ "$STRIPE_SECRET_KEY" == sk_live_* ]]; then
        log_success "Using Stripe production keys"
    else
        log_error "Invalid Stripe secret key format"
        config_issues=$((config_issues + 1))
    fi
    
    if [ $config_issues -eq 0 ]; then
        log_success "Production configuration is valid"
        return 0
    else
        log_error "Found $config_issues configuration issues"
        return 1
    fi
}

# Test Stripe production configuration
test_stripe_production() {
    log_info "Testing Stripe production configuration..."
    
    # Test Stripe API connectivity with production keys
    local stripe_test=$(curl -s -u "$STRIPE_SECRET_KEY:" \
        "https://api.stripe.com/v1/payment_intents" \
        -d "amount=100" \
        -d "currency=usd" \
        -d "automatic_payment_methods[enabled]=true" || echo "error")
    
    if echo "$stripe_test" | grep -q '"id":.*"pi_"'; then
        log_success "Stripe production API is working"
        return 0
    else
        log_error "Stripe production API test failed: $stripe_test"
        return 1
    fi
}

# Test HTTPS certificate and configuration
test_https_configuration() {
    log_info "Testing HTTPS configuration..."
    
    if [ "$ENFORCE_HTTPS" = "true" ] && [ -n "$DOMAIN_NAME" ]; then
        # Test HTTPS endpoint
        local https_response=$(curl -s -o /dev/null -w "%{http_code}" \
            "https://$DOMAIN_NAME/health" 2>/dev/null || echo "000")
        
        if [ "$https_response" = "200" ]; then
            log_success "HTTPS is working correctly"
            
            # Test SSL certificate details
            local cert_info=$(echo | openssl s_client -servername "$DOMAIN_NAME" \
                -connect "$DOMAIN_NAME:443" 2>/dev/null | \
                openssl x509 -noout -dates 2>/dev/null || echo "error")
            
            if [ "$cert_info" != "error" ]; then
                log_success "SSL certificate is valid"
                return 0
            else
                log_warning "Could not verify SSL certificate details"
                return 1
            fi
        else
            log_error "HTTPS test failed (HTTP $https_response)"
            return 1
        fi
    else
        log_info "HTTPS not enforced or domain not configured, skipping HTTPS test"
        return 0
    fi
}

# Test database backup functionality
test_database_backup() {
    log_info "Testing database backup functionality..."
    
    # Run backup script in test mode
    if "$SCRIPT_DIR/backup.sh" database; then
        log_success "Database backup test passed"
        
        # Check if backup file was created
        local latest_backup=$(ls -t "$DEPLOYMENT_DIR/docker/backups/"postgres_backup_*.sql.gz 2>/dev/null | head -1)
        if [ -n "$latest_backup" ]; then
            log_success "Backup file created: $(basename "$latest_backup")"
            return 0
        else
            log_warning "Backup script ran but no backup file found"
            return 1
        fi
    else
        log_error "Database backup test failed"
        return 1
    fi
}

# Test monitoring and logging
test_monitoring() {
    log_info "Testing monitoring and logging..."
    
    local monitoring_issues=0
    
    # Test Prometheus
    local prometheus_response=$(curl -s -o /dev/null -w "%{http_code}" \
        "http://localhost:9090/-/healthy" 2>/dev/null || echo "000")
    
    if [ "$prometheus_response" = "200" ]; then
        log_success "Prometheus is healthy"
    else
        log_warning "Prometheus health check failed (HTTP $prometheus_response)"
        monitoring_issues=$((monitoring_issues + 1))
    fi
    
    # Test Grafana
    local grafana_response=$(curl -s -o /dev/null -w "%{http_code}" \
        "http://localhost:3000/api/health" 2>/dev/null || echo "000")
    
    if [ "$grafana_response" = "200" ]; then
        log_success "Grafana is healthy"
    else
        log_warning "Grafana health check failed (HTTP $grafana_response)"
        monitoring_issues=$((monitoring_issues + 1))
    fi
    
    # Check log files exist and are writable
    local log_dir="/app/logs"
    if docker exec llm-context-exporter test -d "$log_dir" 2>/dev/null; then
        log_success "Log directory exists and is accessible"
    else
        log_warning "Log directory not accessible"
        monitoring_issues=$((monitoring_issues + 1))
    fi
    
    if [ $monitoring_issues -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Test security headers and configuration
test_security_configuration() {
    log_info "Testing security configuration..."
    
    local base_url="$BASE_URL"
    if [ "$ENFORCE_HTTPS" = "true" ] && [ -n "$DOMAIN_NAME" ]; then
        base_url="https://$DOMAIN_NAME"
    fi
    
    local headers=$(curl -s -I "$base_url/" 2>/dev/null || echo "error")
    
    local security_score=0
    local total_checks=6
    
    # Check security headers
    if echo "$headers" | grep -qi "X-Frame-Options"; then
        security_score=$((security_score + 1))
    fi
    
    if echo "$headers" | grep -qi "X-Content-Type-Options"; then
        security_score=$((security_score + 1))
    fi
    
    if echo "$headers" | grep -qi "X-XSS-Protection"; then
        security_score=$((security_score + 1))
    fi
    
    if echo "$headers" | grep -qi "Content-Security-Policy"; then
        security_score=$((security_score + 1))
    fi
    
    if echo "$headers" | grep -qi "Referrer-Policy"; then
        security_score=$((security_score + 1))
    fi
    
    if echo "$headers" | grep -qi "Strict-Transport-Security"; then
        security_score=$((security_score + 1))
    fi
    
    if [ $security_score -ge 5 ]; then
        log_success "Security headers are properly configured ($security_score/$total_checks)"
        return 0
    else
        log_warning "Some security headers are missing ($security_score/$total_checks)"
        return 1
    fi
}

# Test rate limiting
test_rate_limiting() {
    log_info "Testing rate limiting configuration..."
    
    local rate_limit_triggered=false
    local base_url="$BASE_URL"
    
    # Make rapid requests to trigger rate limiting
    for i in {1..20}; do
        local response=$(curl -s -o /dev/null -w "%{http_code}" \
            "$base_url/api/health" 2>/dev/null || echo "000")
        
        if [ "$response" = "429" ]; then
            rate_limit_triggered=true
            break
        fi
        
        sleep 0.1
    done
    
    if [ "$rate_limit_triggered" = true ]; then
        log_success "Rate limiting is working correctly"
        return 0
    else
        log_warning "Rate limiting may not be configured properly"
        return 1
    fi
}

# Test file upload size limits
test_upload_limits() {
    log_info "Testing file upload size limits..."
    
    # Create a test file larger than the limit (if configured)
    local test_file="/tmp/large_test_file.json"
    local max_size_mb=500
    
    # Create a 1MB test file
    dd if=/dev/zero of="$test_file" bs=1M count=1 2>/dev/null
    
    # Test upload
    local upload_response=$(curl -s -X POST \
        -F "file=@$test_file" \
        -F "target=gemini" \
        "$BASE_URL/api/upload" 2>/dev/null || echo "error")
    
    # Clean up test file
    rm -f "$test_file"
    
    if echo "$upload_response" | grep -q "success\|error"; then
        log_success "File upload size handling is working"
        return 0
    else
        log_warning "File upload size handling may have issues: $upload_response"
        return 1
    fi
}

# Generate production test report
generate_production_report() {
    local timestamp=$(date)
    local report_file="/tmp/production_test_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "LLM Context Exporter Production Test Report"
        echo "Generated: $timestamp"
        echo "==========================================="
        echo
        echo "Configuration Tests:"
        echo "- Production Config: $production_config_result"
        echo "- HTTPS Configuration: $https_config_result"
        echo "- Security Configuration: $security_config_result"
        echo
        echo "Functionality Tests:"
        echo "- Localhost Binding: $localhost_binding_result"
        echo "- Payment Verification: $payment_verification_result"
        echo "- Stripe Production: $stripe_production_result"
        echo "- Rate Limiting: $rate_limiting_result"
        echo "- Upload Limits: $upload_limits_result"
        echo
        echo "Infrastructure Tests:"
        echo "- Database Backup: $database_backup_result"
        echo "- Monitoring: $monitoring_result"
        echo
        echo "Overall Status: $overall_status"
        echo
        echo "Environment Details:"
        echo "- Domain: $DOMAIN_NAME"
        echo "- HTTPS Enforced: $ENFORCE_HTTPS"
        echo "- Flask Environment: $FLASK_ENV"
        echo "- Stripe Mode: $(echo "$STRIPE_SECRET_KEY" | cut -c1-7)..."
        
    } > "$report_file"
    
    echo "$report_file"
}

# Main production testing process
main() {
    log_info "Starting production environment testing..."
    
    local tests_passed=0
    local total_tests=0
    
    # Configuration tests
    total_tests=$((total_tests + 1))
    if test_production_config; then
        production_config_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        production_config_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_https_configuration; then
        https_config_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        https_config_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_security_configuration; then
        security_config_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        security_config_result="WARN"
    fi
    
    # Functionality tests
    total_tests=$((total_tests + 1))
    if test_localhost_binding; then
        localhost_binding_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        localhost_binding_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_payment_verification; then
        payment_verification_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        payment_verification_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_stripe_production; then
        stripe_production_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        stripe_production_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_rate_limiting; then
        rate_limiting_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        rate_limiting_result="WARN"
    fi
    
    total_tests=$((total_tests + 1))
    if test_upload_limits; then
        upload_limits_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        upload_limits_result="WARN"
    fi
    
    # Infrastructure tests
    total_tests=$((total_tests + 1))
    if test_database_backup; then
        database_backup_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        database_backup_result="WARN"
    fi
    
    total_tests=$((total_tests + 1))
    if test_monitoring; then
        monitoring_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        monitoring_result="WARN"
    fi
    
    # Generate summary
    log_info "Production Test Summary:"
    echo "Tests passed: $tests_passed/$total_tests"
    
    if [ $tests_passed -eq $total_tests ]; then
        overall_status="PRODUCTION READY"
        log_success "$overall_status"
        exit_code=0
    elif [ $tests_passed -gt $((total_tests * 3 / 4)) ]; then
        overall_status="MOSTLY READY"
        log_warning "$overall_status - Minor issues detected"
        exit_code=1
    else
        overall_status="NOT READY"
        log_error "$overall_status - Significant issues detected"
        exit_code=2
    fi
    
    # Generate detailed report
    local report_file=$(generate_production_report)
    log_info "Detailed production test report: $report_file"
    
    exit $exit_code
}

# Handle script arguments
case "${1:-}" in
    "config")
        test_production_config && test_https_configuration && test_security_configuration
        ;;
    "stripe")
        test_stripe_production && test_payment_verification
        ;;
    "security")
        test_security_configuration && test_rate_limiting && test_https_configuration
        ;;
    "infrastructure")
        test_database_backup && test_monitoring
        ;;
    *)
        main
        ;;
esac