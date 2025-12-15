#!/bin/bash

# Database Backup Script for LLM Context Exporter
# This script creates encrypted backups of the PostgreSQL database

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
BACKUP_DIR="$DEPLOYMENT_DIR/docker/backups"
DATE=$(date +%Y%m%d_%H%M%S)

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

# Create backup directory
mkdir -p "$BACKUP_DIR"

backup_database() {
    log_info "Starting database backup..."
    
    local backup_file="$BACKUP_DIR/postgres_backup_$DATE.sql"
    local compressed_file="$backup_file.gz"
    
    # Create database dump
    docker exec llm-context-postgres pg_dump \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        --no-password \
        > "$backup_file"
    
    if [ $? -eq 0 ]; then
        log_success "Database dump created: $backup_file"
        
        # Compress the backup
        gzip "$backup_file"
        log_success "Backup compressed: $compressed_file"
        
        # Upload to S3 if configured
        if [ "$BACKUP_ENABLED" = "true" ] && [ -n "$BACKUP_S3_BUCKET" ]; then
            upload_to_s3 "$compressed_file"
        fi
        
        return 0
    else
        log_error "Database backup failed"
        return 1
    fi
}

backup_uploads() {
    log_info "Starting uploads backup..."
    
    local backup_file="$BACKUP_DIR/uploads_backup_$DATE.tar.gz"
    
    # Create tar archive of uploads
    docker run --rm \
        -v llm-context-exporter_app_uploads:/uploads:ro \
        -v "$BACKUP_DIR:/backup" \
        alpine:latest \
        tar -czf "/backup/uploads_backup_$DATE.tar.gz" -C /uploads .
    
    if [ $? -eq 0 ]; then
        log_success "Uploads backup created: $backup_file"
        
        # Upload to S3 if configured
        if [ "$BACKUP_ENABLED" = "true" ] && [ -n "$BACKUP_S3_BUCKET" ]; then
            upload_to_s3 "$backup_file"
        fi
        
        return 0
    else
        log_error "Uploads backup failed"
        return 1
    fi
}

upload_to_s3() {
    local file_path="$1"
    local file_name=$(basename "$file_path")
    
    log_info "Uploading $file_name to S3..."
    
    # Check if AWS CLI is available
    if ! command -v aws &> /dev/null; then
        log_warning "AWS CLI not found. Installing..."
        pip install awscli
    fi
    
    # Upload to S3
    aws s3 cp "$file_path" "s3://$BACKUP_S3_BUCKET/backups/$file_name" \
        --region "$AWS_REGION"
    
    if [ $? -eq 0 ]; then
        log_success "Backup uploaded to S3: s3://$BACKUP_S3_BUCKET/backups/$file_name"
    else
        log_error "Failed to upload backup to S3"
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up old backups..."
    
    local retention_days=${BACKUP_RETENTION_DAYS:-30}
    
    # Remove local backups older than retention period
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$retention_days -delete
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$retention_days -delete
    
    log_success "Old local backups cleaned up (older than $retention_days days)"
    
    # Clean up S3 backups if configured
    if [ "$BACKUP_ENABLED" = "true" ] && [ -n "$BACKUP_S3_BUCKET" ]; then
        aws s3 ls "s3://$BACKUP_S3_BUCKET/backups/" | \
        while read -r line; do
            create_date=$(echo "$line" | awk '{print $1" "$2}')
            file_name=$(echo "$line" | awk '{print $4}')
            
            if [ -n "$file_name" ]; then
                create_timestamp=$(date -d "$create_date" +%s)
                current_timestamp=$(date +%s)
                age_days=$(( (current_timestamp - create_timestamp) / 86400 ))
                
                if [ $age_days -gt $retention_days ]; then
                    aws s3 rm "s3://$BACKUP_S3_BUCKET/backups/$file_name"
                    log_info "Removed old S3 backup: $file_name"
                fi
            fi
        done
    fi
}

verify_backup() {
    local backup_file="$1"
    
    log_info "Verifying backup integrity..."
    
    # Test if the compressed file is valid
    if gzip -t "$backup_file" 2>/dev/null; then
        log_success "Backup file integrity verified"
        return 0
    else
        log_error "Backup file is corrupted"
        return 1
    fi
}

send_notification() {
    local status="$1"
    local message="$2"
    
    # Send email notification if SMTP is configured
    if [ -n "$SMTP_SERVER" ] && [ -n "$FROM_EMAIL" ]; then
        local subject="LLM Context Exporter Backup $status"
        
        echo "$message" | mail -s "$subject" \
            -S smtp="$SMTP_SERVER:$SMTP_PORT" \
            -S smtp-use-starttls \
            -S smtp-auth=login \
            -S smtp-auth-user="$SMTP_USERNAME" \
            -S smtp-auth-password="$SMTP_PASSWORD" \
            -S from="$FROM_EMAIL" \
            "$FROM_EMAIL"
    fi
}

# Main backup process
main() {
    log_info "Starting backup process..."
    
    local backup_success=true
    local backup_files=()
    
    # Backup database
    if backup_database; then
        backup_files+=("postgres_backup_$DATE.sql.gz")
    else
        backup_success=false
    fi
    
    # Backup uploads
    if backup_uploads; then
        backup_files+=("uploads_backup_$DATE.tar.gz")
    else
        backup_success=false
    fi
    
    # Verify backups
    for file in "${backup_files[@]}"; do
        if ! verify_backup "$BACKUP_DIR/$file"; then
            backup_success=false
        fi
    done
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Send notification
    if [ "$backup_success" = true ]; then
        local message="Backup completed successfully at $(date). Files: ${backup_files[*]}"
        log_success "$message"
        send_notification "SUCCESS" "$message"
    else
        local message="Backup failed at $(date). Please check the logs."
        log_error "$message"
        send_notification "FAILED" "$message"
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    "database")
        backup_database
        ;;
    "uploads")
        backup_uploads
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    *)
        main
        ;;
esac