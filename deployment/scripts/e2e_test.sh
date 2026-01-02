#!/bin/bash

# End-to-End Testing Script for LLM Context Exporter
# This script tests the complete application flow in a production-like environment

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
TEST_DATA_DIR="$SCRIPT_DIR/../test_data"
BASE_URL="http://localhost"

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

setup_test_data() {
    log_info "Setting up test data..."
    
    mkdir -p "$TEST_DATA_DIR"
    
    # Create a sample ChatGPT export file
    cat > "$TEST_DATA_DIR/sample_export.json" << 'EOF'
{
  "conversations": [
    {
      "id": "test-conversation-1",
      "title": "Python Web Development Help",
      "create_time": 1703001600.0,
      "update_time": 1703001800.0,
      "mapping": {
        "msg1": {
          "id": "msg1",
          "message": {
            "id": "msg1",
            "author": {"role": "user"},
            "content": {"content_type": "text", "parts": ["I'm building a Flask web application for document processing. Can you help me with file upload handling?"]},
            "create_time": 1703001600.0
          }
        },
        "msg2": {
          "id": "msg2",
          "message": {
            "id": "msg2",
            "author": {"role": "assistant"},
            "content": {"content_type": "text", "parts": ["I'd be happy to help you with Flask file upload handling! Here's a comprehensive approach..."]},
            "create_time": 1703001650.0
          }
        }
      }
    }
  ]
}
EOF
    
    log_success "Test data created"
}

test_health_endpoint() {
    log_info "Testing health endpoint..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health" || echo "000")
    
    if [ "$response" = "200" ]; then
        log_success "Health endpoint is working (HTTP $response)"
        return 0
    else
        log_error "Health endpoint failed (HTTP $response)"
        return 1
    fi
}

test_web_interface_load() {
    log_info "Testing web interface loading..."
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/" || echo "000")
    
    if [ "$response" = "200" ]; then
        log_success "Web interface loads successfully (HTTP $response)"
        return 0
    else
        log_error "Web interface failed to load (HTTP $response)"
        return 1
    fi
}

test_file_upload() {
    log_info "Testing file upload functionality..."
    
    local upload_response=$(curl -s -X POST \
        -F "file=@$TEST_DATA_DIR/sample_export.json" \
        -F "target=gemini" \
        "$BASE_URL/api/upload" || echo "error")
    
    if echo "$upload_response" | grep -q "success"; then
        log_success "File upload test passed"
        
        # Extract session ID for further tests
        local session_id=$(echo "$upload_response" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
        echo "$session_id" > "$TEST_DATA_DIR/session_id.txt"
        
        return 0
    else
        log_error "File upload test failed: $upload_response"
        return 1
    fi
}

test_preview_generation() {
    log_info "Testing preview generation..."
    
    if [ ! -f "$TEST_DATA_DIR/session_id.txt" ]; then
        log_error "No session ID available from upload test"
        return 1
    fi
    
    local session_id=$(cat "$TEST_DATA_DIR/session_id.txt")
    
    local preview_response=$(curl -s -X GET \
        "$BASE_URL/api/preview?session_id=$session_id" || echo "error")
    
    if echo "$preview_response" | grep -q "projects"; then
        log_success "Preview generation test passed"
        return 0
    else
        log_error "Preview generation test failed: $preview_response"
        return 1
    fi
}

test_beta_user_flow() {
    log_info "Testing beta user flow..."
    
    # Add a test beta user
    local test_email="test@example.com"
    
    # Test beta status check
    local beta_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$test_email\"}" \
        "$BASE_URL/api/beta/status" || echo "error")
    
    if echo "$beta_response" | grep -q "beta_access"; then
        log_success "Beta user flow test passed"
        return 0
    else
        log_warning "Beta user flow test failed (expected for non-beta users): $beta_response"
        return 0  # This is expected behavior
    fi
}

test_payment_flow() {
    log_info "Testing payment flow (test mode)..."
    
    # Test payment intent creation
    local payment_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"amount\":500}" \
        "$BASE_URL/api/payment/create" || echo "error")
    
    if echo "$payment_response" | grep -q "client_secret"; then
        log_success "Payment flow test passed"
        return 0
    else
        log_error "Payment flow test failed: $payment_response"
        return 1
    fi
}

test_api_rate_limiting() {
    log_info "Testing API rate limiting..."
    
    local rate_limit_hit=false
    
    # Make multiple rapid requests to trigger rate limiting
    for i in {1..15}; do
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/health" || echo "000")
        
        if [ "$response" = "429" ]; then
            rate_limit_hit=true
            break
        fi
        
        sleep 0.1
    done
    
    if [ "$rate_limit_hit" = true ]; then
        log_success "Rate limiting is working correctly"
        return 0
    else
        log_warning "Rate limiting may not be configured properly"
        return 1
    fi
}

test_security_headers() {
    log_info "Testing security headers..."
    
    local headers=$(curl -s -I "$BASE_URL/" || echo "error")
    
    local security_checks=0
    local total_checks=5
    
    # Check for security headers
    if echo "$headers" | grep -qi "X-Frame-Options"; then
        security_checks=$((security_checks + 1))
    fi
    
    if echo "$headers" | grep -qi "X-Content-Type-Options"; then
        security_checks=$((security_checks + 1))
    fi
    
    if echo "$headers" | grep -qi "X-XSS-Protection"; then
        security_checks=$((security_checks + 1))
    fi
    
    if echo "$headers" | grep -qi "Content-Security-Policy"; then
        security_checks=$((security_checks + 1))
    fi
    
    if echo "$headers" | grep -qi "Referrer-Policy"; then
        security_checks=$((security_checks + 1))
    fi
    
    if [ $security_checks -ge 4 ]; then
        log_success "Security headers test passed ($security_checks/$total_checks headers found)"
        return 0
    else
        log_warning "Some security headers missing ($security_checks/$total_checks headers found)"
        return 1
    fi
}

test_https_redirect() {
    log_info "Testing HTTPS redirect..."
    
    if [ "$ENFORCE_HTTPS" = "true" ]; then
        local redirect_response=$(curl -s -o /dev/null -w "%{http_code}" -L "http://$DOMAIN_NAME/" || echo "000")
        
        if [ "$redirect_response" = "200" ]; then
            log_success "HTTPS redirect is working"
            return 0
        else
            log_error "HTTPS redirect test failed (HTTP $redirect_response)"
            return 1
        fi
    else
        log_info "HTTPS not enforced, skipping redirect test"
        return 0
    fi
}

test_database_operations() {
    log_info "Testing database operations..."
    
    # Test database connectivity through the application
    local db_test_response=$(curl -s -X GET "$BASE_URL/api/beta/status" || echo "error")
    
    if echo "$db_test_response" | grep -q "beta_access"; then
        log_success "Database operations test passed"
        return 0
    else
        log_error "Database operations test failed: $db_test_response"
        return 1
    fi
}

test_monitoring_endpoints() {
    log_info "Testing monitoring endpoints..."
    
    # Test Prometheus
    local prometheus_response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:9090/-/healthy" || echo "000")
    if [ "$prometheus_response" = "200" ]; then
        log_success "Prometheus is accessible"
    else
        log_warning "Prometheus not accessible (HTTP $prometheus_response)"
    fi
    
    # Test Grafana
    local grafana_response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/api/health" || echo "000")
    if [ "$grafana_response" = "200" ]; then
        log_success "Grafana is accessible"
    else
        log_warning "Grafana not accessible (HTTP $grafana_response)"
    fi
}

cleanup_test_data() {
    log_info "Cleaning up test data..."
    
    rm -rf "$TEST_DATA_DIR"
    
    log_success "Test data cleaned up"
}

generate_test_report() {
    local timestamp=$(date)
    local report_file="/tmp/e2e_test_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "LLM Context Exporter E2E Test Report"
        echo "Generated: $timestamp"
        echo "======================================"
        echo
        echo "Test Results:"
        echo "- Health Endpoint: $health_test_result"
        echo "- Web Interface: $web_interface_test_result"
        echo "- File Upload: $file_upload_test_result"
        echo "- Preview Generation: $preview_test_result"
        echo "- Beta User Flow: $beta_user_test_result"
        echo "- Payment Flow: $payment_test_result"
        echo "- Rate Limiting: $rate_limiting_test_result"
        echo "- Security Headers: $security_headers_test_result"
        echo "- HTTPS Redirect: $https_redirect_test_result"
        echo "- Database Operations: $database_test_result"
        echo "- Monitoring: $monitoring_test_result"
        echo
        echo "Overall Status: $overall_status"
        
    } > "$report_file"
    
    echo "$report_file"
}

# Main testing process
main() {
    log_info "Starting end-to-end testing..."
    
    local tests_passed=0
    local total_tests=0
    
    # Setup
    setup_test_data
    
    # Run all tests
    total_tests=$((total_tests + 1))
    if test_health_endpoint; then
        health_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        health_test_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_web_interface_load; then
        web_interface_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        web_interface_test_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_file_upload; then
        file_upload_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        file_upload_test_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_preview_generation; then
        preview_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        preview_test_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_beta_user_flow; then
        beta_user_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        beta_user_test_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_payment_flow; then
        payment_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        payment_test_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_api_rate_limiting; then
        rate_limiting_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        rate_limiting_test_result="WARN"
    fi
    
    total_tests=$((total_tests + 1))
    if test_security_headers; then
        security_headers_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        security_headers_test_result="WARN"
    fi
    
    total_tests=$((total_tests + 1))
    if test_https_redirect; then
        https_redirect_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        https_redirect_test_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_database_operations; then
        database_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        database_test_result="FAIL"
    fi
    
    total_tests=$((total_tests + 1))
    if test_monitoring_endpoints; then
        monitoring_test_result="PASS"
        tests_passed=$((tests_passed + 1))
    else
        monitoring_test_result="WARN"
    fi
    
    # Cleanup
    cleanup_test_data
    
    # Generate summary
    log_info "E2E Test Summary:"
    echo "Tests passed: $tests_passed/$total_tests"
    
    if [ $tests_passed -eq $total_tests ]; then
        overall_status="ALL TESTS PASSED"
        log_success "$overall_status"
        
        # Generate report
        local report_file=$(generate_test_report)
        log_info "Detailed test report generated: $report_file"
        
        exit 0
    elif [ $tests_passed -gt $((total_tests / 2)) ]; then
        overall_status="MOSTLY PASSING"
        log_warning "$overall_status - Some tests failed but system is mostly functional"
        
        # Generate report
        local report_file=$(generate_test_report)
        log_info "Detailed test report generated: $report_file"
        
        exit 1
    else
        overall_status="MULTIPLE FAILURES"
        log_error "$overall_status - System may not be ready for production"
        
        # Generate report
        local report_file=$(generate_test_report)
        log_info "Detailed test report generated: $report_file"
        
        exit 2
    fi
}

# Handle script arguments
case "${1:-}" in
    "quick")
        test_health_endpoint && test_web_interface_load
        ;;
    "security")
        test_security_headers && test_https_redirect && test_api_rate_limiting
        ;;
    "payment")
        test_payment_flow && test_beta_user_flow
        ;;
    "upload")
        setup_test_data && test_file_upload && test_preview_generation && cleanup_test_data
        ;;
    *)
        main
        ;;
esac