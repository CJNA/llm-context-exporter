# Admin Guide for Beta Management

This guide covers the administrative features for managing beta users, tracking usage, and collecting feedback for the LLM Context Exporter.

## Table of Contents

- [Overview](#overview)
- [Beta User Management](#beta-user-management)
- [Usage Tracking](#usage-tracking)
- [Feedback Collection](#feedback-collection)
- [Reporting and Analytics](#reporting-and-analytics)
- [Payment Management](#payment-management)
- [Database Management](#database-management)
- [Monitoring and Alerts](#monitoring-and-alerts)
- [Security Considerations](#security-considerations)

## Overview

The LLM Context Exporter includes a comprehensive beta management system that allows administrators to:

- Manage beta user access and permissions
- Track usage statistics and patterns
- Collect and analyze user feedback
- Generate reports for product development
- Monitor system performance and usage

### Architecture

The beta management system consists of:
- **BetaManager**: Core beta user management
- **PaymentManager**: Payment processing and verification
- **Admin CLI**: Command-line interface for administration
- **Web Dashboard**: Browser-based admin interface (optional)
- **Database**: SQLite database for data storage

## Beta User Management

### Adding Beta Users

#### Via CLI

```bash
# Add a single beta user
llm-context-export admin add-user \
  --email user@example.com \
  --notes "Early adopter, power user interested in Ollama"

# Add multiple users from a file
llm-context-export admin add-users \
  --file beta_users.csv
```

#### Via Python API

```python
from llm_context_exporter.web.beta import BetaManager

# Initialize manager
manager = BetaManager()

# Add beta user
manager.add_beta_user(
    email="user@example.com",
    notes="Early adopter, power user"
)

# Add multiple users
users = [
    ("alice@example.com", "Developer, interested in CLI"),
    ("bob@example.com", "Designer, prefers web interface"),
    ("carol@example.com", "Data scientist, Ollama user")
]

for email, notes in users:
    manager.add_beta_user(email, notes)
```

### Listing Beta Users

```bash
# List all beta users
llm-context-export admin list-users

# List with detailed information
llm-context-export admin list-users --verbose

# Filter by activity
llm-context-export admin list-users --active-only
llm-context-export admin list-users --inactive-only
```

### Removing Beta Users

```bash
# Remove a single user
llm-context-export admin remove-user --email user@example.com

# Remove multiple users
llm-context-export admin remove-users --file remove_list.txt

# Remove inactive users (no exports in 30 days)
llm-context-export admin cleanup-users --inactive-days 30
```

### User Information Management

```bash
# Update user notes
llm-context-export admin update-user \
  --email user@example.com \
  --notes "Updated: Power user, provides excellent feedback"

# View detailed user information
llm-context-export admin user-info --email user@example.com
```

## Usage Tracking

### Automatic Usage Recording

The system automatically tracks:
- Export attempts and completions
- Target platforms used (Gemini vs Ollama)
- File sizes processed
- Processing times
- Error rates
- Feature usage patterns

### Manual Usage Recording

```python
from llm_context_exporter.web.beta import BetaManager

manager = BetaManager()

# Record an export
manager.record_export(
    email="user@example.com",
    target_platform="gemini",
    conversations_processed=45,
    export_size_mb=3.2,
    processing_time_seconds=12.5,
    success=True
)

# Record an error
manager.record_export(
    email="user@example.com",
    target_platform="ollama",
    conversations_processed=0,
    export_size_mb=0,
    processing_time_seconds=5.0,
    success=False,
    error_message="Ollama not installed"
)
```

### Usage Statistics

```bash
# View statistics for a specific user
llm-context-export admin user-stats --email user@example.com

# View aggregate statistics
llm-context-export admin stats --summary

# View platform usage breakdown
llm-context-export admin stats --by-platform

# View usage over time
llm-context-export admin stats --time-range "2024-01-01,2024-01-31"
```

### Usage Patterns Analysis

```python
from llm_context_exporter.web.beta import BetaManager
import pandas as pd

manager = BetaManager()

# Get all usage data
usage_data = manager.get_all_usage_data()

# Convert to DataFrame for analysis
df = pd.DataFrame([
    {
        'email': record.email,
        'platform': record.target_platform,
        'date': record.timestamp.date(),
        'conversations': record.conversations_processed,
        'size_mb': record.export_size_mb,
        'success': record.success
    }
    for record in usage_data
])

# Analyze patterns
print("Platform preferences:")
print(df.groupby('platform').size())

print("\nAverage export size by platform:")
print(df.groupby('platform')['size_mb'].mean())

print("\nSuccess rates by platform:")
print(df.groupby('platform')['success'].mean())

print("\nMost active users:")
print(df.groupby('email').size().sort_values(ascending=False).head(10))
```

## Feedback Collection

### Feedback Collection Methods

#### Automatic Collection (Web Interface)

The web interface automatically prompts beta users for feedback after successful exports:

```python
# Feedback is automatically recorded when submitted via web interface
# No additional code needed - handled by the web app
```

#### Manual Feedback Recording

```python
from llm_context_exporter.web.beta import BetaManager

manager = BetaManager()

# Record feedback
manager.record_feedback(
    email="user@example.com",
    feedback_text="Great tool! Love the privacy-first approach. Ollama setup was a bit tricky but works well once configured.",
    rating=4,
    export_id="export_12345",
    target_platform="ollama"
)
```

#### CLI Feedback Collection

```bash
# View all feedback
llm-context-export admin feedback

# View feedback by rating
llm-context-export admin feedback --rating 5
llm-context-export admin feedback --rating 1

# View feedback by platform
llm-context-export admin feedback --platform gemini
llm-context-export admin feedback --platform ollama

# View recent feedback
llm-context-export admin feedback --recent 7  # Last 7 days
```

### Feedback Analysis

```python
from llm_context_exporter.web.beta import BetaManager
from collections import Counter
import matplotlib.pyplot as plt

manager = BetaManager()

# Get all feedback
feedback = manager.get_all_feedback()

# Rating distribution
ratings = [f.rating for f in feedback]
rating_counts = Counter(ratings)

print("Rating distribution:")
for rating in range(1, 6):
    count = rating_counts.get(rating, 0)
    percentage = (count / len(feedback) * 100) if feedback else 0
    print(f"  {rating} stars: {count} ({percentage:.1f}%)")

# Platform satisfaction
platform_ratings = {}
for f in feedback:
    if f.target_platform not in platform_ratings:
        platform_ratings[f.target_platform] = []
    platform_ratings[f.target_platform].append(f.rating)

print("\nAverage rating by platform:")
for platform, ratings in platform_ratings.items():
    avg_rating = sum(ratings) / len(ratings)
    print(f"  {platform.title()}: {avg_rating:.2f} ({len(ratings)} reviews)")

# Common themes in feedback
feedback_text = [f.feedback_text.lower() for f in feedback]
positive_keywords = ['great', 'love', 'excellent', 'amazing', 'perfect']
negative_keywords = ['difficult', 'confusing', 'slow', 'error', 'problem']

positive_mentions = sum(1 for text in feedback_text if any(word in text for word in positive_keywords))
negative_mentions = sum(1 for text in feedback_text if any(word in text for word in negative_keywords))

print(f"\nSentiment analysis:")
print(f"  Positive mentions: {positive_mentions}")
print(f"  Negative mentions: {negative_mentions}")
```

### Feedback Response Management

```python
# Track feedback responses (if implementing follow-up system)
class FeedbackResponse:
    def __init__(self, feedback_id, response_text, admin_email):
        self.feedback_id = feedback_id
        self.response_text = response_text
        self.admin_email = admin_email
        self.timestamp = datetime.now()

# Example: Responding to low-rated feedback
low_rated_feedback = [f for f in feedback if f.rating <= 2]

for f in low_rated_feedback:
    print(f"Low rating from {f.email}: {f.feedback_text}")
    # Could trigger email or in-app notification for follow-up
```

## Reporting and Analytics

### Generate Usage Reports

```bash
# Generate comprehensive report
llm-context-export admin report \
  --output beta_report.csv \
  --format csv \
  --include-feedback

# Generate JSON report for API consumption
llm-context-export admin report \
  --output beta_report.json \
  --format json \
  --time-range "2024-01-01,2024-01-31"

# Generate summary report
llm-context-export admin report \
  --summary-only \
  --output summary.txt
```

### Custom Analytics

```python
from llm_context_exporter.web.beta import BetaManager
import json
from datetime import datetime, timedelta

def generate_analytics_report(manager: BetaManager, days: int = 30):
    """Generate comprehensive analytics report."""
    
    # Get data
    users = manager.get_beta_users()
    feedback = manager.get_all_feedback()
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Filter recent data
    recent_feedback = [f for f in feedback if f.timestamp >= start_date]
    
    # User statistics
    total_users = len(users)
    active_users = len([u for u in users if u.total_exports > 0])
    new_users = len([u for u in users if u.added_date >= start_date])
    
    # Usage statistics
    total_exports = sum(u.total_exports for u in users)
    total_feedback = len(feedback)
    recent_feedback_count = len(recent_feedback)
    
    # Platform breakdown
    platform_stats = {}
    for user in users:
        user_stats = manager.get_usage_stats(user.email)
        for platform, count in user_stats.exports_by_target.items():
            platform_stats[platform] = platform_stats.get(platform, 0) + count
    
    # Rating statistics
    if recent_feedback:
        avg_rating = sum(f.rating for f in recent_feedback) / len(recent_feedback)
        rating_distribution = {}
        for f in recent_feedback:
            rating_distribution[f.rating] = rating_distribution.get(f.rating, 0) + 1
    else:
        avg_rating = 0
        rating_distribution = {}
    
    # Generate report
    report = {
        'report_date': end_date.isoformat(),
        'period_days': days,
        'user_statistics': {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_period': new_users,
            'activation_rate': (active_users / total_users * 100) if total_users > 0 else 0
        },
        'usage_statistics': {
            'total_exports': total_exports,
            'exports_per_user': total_exports / total_users if total_users > 0 else 0,
            'platform_breakdown': platform_stats
        },
        'feedback_statistics': {
            'total_feedback': total_feedback,
            'recent_feedback': recent_feedback_count,
            'average_rating': avg_rating,
            'rating_distribution': rating_distribution,
            'feedback_rate': (total_feedback / total_exports * 100) if total_exports > 0 else 0
        },
        'top_users': [
            {
                'email': user.email,
                'exports': user.total_exports,
                'feedback_count': user.feedback_count
            }
            for user in sorted(users, key=lambda u: u.total_exports, reverse=True)[:10]
        ]
    }
    
    return report

# Usage
manager = BetaManager()
report = generate_analytics_report(manager, days=30)

# Save report
with open('analytics_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"Analytics Report Generated:")
print(f"Total Users: {report['user_statistics']['total_users']}")
print(f"Active Users: {report['user_statistics']['active_users']}")
print(f"Average Rating: {report['feedback_statistics']['average_rating']:.2f}")
```

### Dashboard Metrics

Key metrics to track on an admin dashboard:

```python
def get_dashboard_metrics(manager: BetaManager):
    """Get key metrics for admin dashboard."""
    
    users = manager.get_beta_users()
    feedback = manager.get_all_feedback()
    
    # Current metrics
    metrics = {
        'total_users': len(users),
        'active_users': len([u for u in users if u.total_exports > 0]),
        'total_exports': sum(u.total_exports for u in users),
        'total_feedback': len(feedback),
        'average_rating': sum(f.rating for f in feedback) / len(feedback) if feedback else 0,
        'platform_split': {
            'gemini': 0,
            'ollama': 0
        }
    }
    
    # Platform usage
    for user in users:
        user_stats = manager.get_usage_stats(user.email)
        for platform, count in user_stats.exports_by_target.items():
            if platform in metrics['platform_split']:
                metrics['platform_split'][platform] += count
    
    # Recent activity (last 7 days)
    recent_date = datetime.now() - timedelta(days=7)
    recent_users = [u for u in users if u.last_export_date and u.last_export_date >= recent_date]
    recent_feedback = [f for f in feedback if f.timestamp >= recent_date]
    
    metrics['recent_activity'] = {
        'active_users_7d': len(recent_users),
        'new_feedback_7d': len(recent_feedback)
    }
    
    return metrics

# Usage
metrics = get_dashboard_metrics(manager)
print(f"Dashboard Metrics: {json.dumps(metrics, indent=2, default=str)}")
```

## Payment Management

### Payment Verification

```python
from llm_context_exporter.core.payment import PaymentManager

payment_manager = PaymentManager()

# Verify payment for user
def verify_user_payment(email: str, payment_intent_id: str) -> bool:
    """Verify payment for a specific user."""
    try:
        is_verified = payment_manager.verify_payment(payment_intent_id)
        if is_verified:
            # Record successful payment
            print(f"Payment verified for {email}: {payment_intent_id}")
            return True
        else:
            print(f"Payment verification failed for {email}: {payment_intent_id}")
            return False
    except Exception as e:
        print(f"Payment verification error for {email}: {e}")
        return False

# Check payment requirements
def check_payment_requirements(email: str) -> dict:
    """Check if user needs to pay."""
    user_context = {'source': 'web', 'email': email}
    
    requires_payment = payment_manager.requires_payment(user_context)
    is_beta = payment_manager.is_beta_user(email)
    
    return {
        'requires_payment': requires_payment,
        'is_beta_user': is_beta,
        'reason': 'beta_user' if is_beta else 'regular_user' if requires_payment else 'cli_user'
    }
```

### Payment Analytics

```bash
# View payment statistics
llm-context-export admin payment-stats

# View failed payments
llm-context-export admin payment-stats --failed-only

# Generate payment report
llm-context-export admin payment-report \
  --output payment_report.csv \
  --time-range "2024-01-01,2024-01-31"
```

## Database Management

### Database Backup

```python
import shutil
from datetime import datetime

def backup_beta_database(db_path: str, backup_dir: str):
    """Create backup of beta user database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"beta_db_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    shutil.copy2(db_path, backup_path)
    print(f"Database backed up to: {backup_path}")
    return backup_path

# Usage
backup_path = backup_beta_database("beta_users.db", "./backups")
```

### Database Maintenance

```bash
# Vacuum database to reclaim space
llm-context-export admin db-maintenance --vacuum

# Check database integrity
llm-context-export admin db-maintenance --check-integrity

# Export database to CSV
llm-context-export admin db-export --output beta_data.csv

# Import data from CSV
llm-context-export admin db-import --input beta_data.csv
```

### Data Migration

```python
def migrate_beta_data(old_db_path: str, new_db_path: str):
    """Migrate beta data between database versions."""
    
    # Initialize managers
    old_manager = BetaManager(old_db_path)
    new_manager = BetaManager(new_db_path)
    
    # Get all data from old database
    old_users = old_manager.get_beta_users()
    old_feedback = old_manager.get_all_feedback()
    
    # Migrate users
    for user in old_users:
        new_manager.add_beta_user(user.email, user.notes)
        
        # Migrate usage stats
        stats = old_manager.get_usage_stats(user.email)
        for platform, count in stats.exports_by_target.items():
            for _ in range(count):
                new_manager.record_export(
                    user.email, 
                    platform, 
                    conversations_processed=0,  # Historical data may not have this
                    export_size_mb=0
                )
    
    # Migrate feedback
    for feedback in old_feedback:
        new_manager.record_feedback(
            feedback.email,
            feedback.feedback_text,
            feedback.rating,
            feedback.export_id,
            feedback.target_platform
        )
    
    print(f"Migrated {len(old_users)} users and {len(old_feedback)} feedback entries")
```

## Monitoring and Alerts

### System Health Monitoring

```python
import psutil
import logging
from datetime import datetime

def monitor_system_health():
    """Monitor system health and resource usage."""
    
    # CPU and memory usage
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database size
    db_size = os.path.getsize("beta_users.db") / (1024 * 1024)  # MB
    
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'memory_available_gb': memory.available / (1024**3),
        'disk_percent': disk.percent,
        'disk_free_gb': disk.free / (1024**3),
        'database_size_mb': db_size
    }
    
    # Check for alerts
    alerts = []
    if cpu_percent > 80:
        alerts.append(f"High CPU usage: {cpu_percent}%")
    if memory.percent > 85:
        alerts.append(f"High memory usage: {memory.percent}%")
    if disk.percent > 90:
        alerts.append(f"Low disk space: {disk.percent}% used")
    
    health_status['alerts'] = alerts
    
    return health_status

# Usage
health = monitor_system_health()
if health['alerts']:
    print("System alerts:")
    for alert in health['alerts']:
        print(f"  ⚠️  {alert}")
```

### Usage Alerts

```python
def check_usage_alerts(manager: BetaManager):
    """Check for unusual usage patterns that may need attention."""
    
    users = manager.get_beta_users()
    alerts = []
    
    # Check for inactive users
    inactive_threshold = datetime.now() - timedelta(days=30)
    inactive_users = [
        u for u in users 
        if not u.last_export_date or u.last_export_date < inactive_threshold
    ]
    
    if len(inactive_users) > len(users) * 0.5:  # More than 50% inactive
        alerts.append(f"High inactive user rate: {len(inactive_users)}/{len(users)} users inactive")
    
    # Check for users with many failed exports
    for user in users:
        # This would require tracking failed exports in the database
        # Implementation depends on your specific tracking needs
        pass
    
    # Check for low feedback rates
    total_exports = sum(u.total_exports for u in users)
    total_feedback = sum(u.feedback_count for u in users)
    feedback_rate = (total_feedback / total_exports * 100) if total_exports > 0 else 0
    
    if feedback_rate < 10:  # Less than 10% feedback rate
        alerts.append(f"Low feedback rate: {feedback_rate:.1f}%")
    
    return alerts

# Usage
alerts = check_usage_alerts(manager)
for alert in alerts:
    print(f"📊 {alert}")
```

## Security Considerations

### Access Control

```python
import hashlib
import secrets

class AdminAuth:
    """Simple admin authentication system."""
    
    def __init__(self, admin_password_hash: str):
        self.admin_password_hash = admin_password_hash
    
    def verify_admin(self, password: str) -> bool:
        """Verify admin password."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.admin_password_hash
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storage."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a secure random password."""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

# Usage
admin_password = AdminAuth.generate_secure_password()
admin_hash = AdminAuth.hash_password(admin_password)
auth = AdminAuth(admin_hash)

print(f"Generated admin password: {admin_password}")
print(f"Store this hash: {admin_hash}")
```

### Data Privacy

```python
def anonymize_user_data(manager: BetaManager, user_email: str):
    """Anonymize user data for privacy compliance."""
    
    # Generate anonymous ID
    anonymous_id = hashlib.sha256(user_email.encode()).hexdigest()[:16]
    
    # Get user data
    user = next((u for u in manager.get_beta_users() if u.email == user_email), None)
    if not user:
        return None
    
    # Create anonymized record
    anonymized_data = {
        'anonymous_id': anonymous_id,
        'added_date': user.added_date,
        'total_exports': user.total_exports,
        'feedback_count': user.feedback_count,
        'last_export_date': user.last_export_date
    }
    
    # Remove original user data
    manager.remove_beta_user(user_email)
    
    return anonymized_data

def export_gdpr_data(manager: BetaManager, user_email: str):
    """Export all data for a user (GDPR compliance)."""
    
    # Get user data
    user = next((u for u in manager.get_beta_users() if u.email == user_email), None)
    if not user:
        return None
    
    # Get usage stats
    stats = manager.get_usage_stats(user_email)
    
    # Get feedback
    user_feedback = [f for f in manager.get_all_feedback() if f.email == user_email]
    
    # Compile all data
    gdpr_data = {
        'user_profile': {
            'email': user.email,
            'added_date': user.added_date.isoformat(),
            'notes': user.notes,
            'total_exports': user.total_exports,
            'last_export_date': user.last_export_date.isoformat() if user.last_export_date else None
        },
        'usage_statistics': {
            'total_exports': stats.total_exports,
            'exports_by_platform': stats.exports_by_target,
            'total_conversations_processed': stats.total_conversations_processed,
            'average_export_size_mb': stats.average_export_size_mb
        },
        'feedback': [
            {
                'timestamp': f.timestamp.isoformat(),
                'rating': f.rating,
                'feedback_text': f.feedback_text,
                'target_platform': f.target_platform,
                'export_id': f.export_id
            }
            for f in user_feedback
        ]
    }
    
    return gdpr_data
```

### Audit Logging

```python
import logging
from datetime import datetime

# Set up audit logging
audit_logger = logging.getLogger('admin_audit')
audit_handler = logging.FileHandler('admin_audit.log')
audit_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

def log_admin_action(action: str, details: dict, admin_user: str = "system"):
    """Log administrative actions for audit trail."""
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'admin_user': admin_user,
        'action': action,
        'details': details
    }
    
    audit_logger.info(f"ADMIN_ACTION: {json.dumps(log_entry)}")

# Usage examples
log_admin_action("ADD_BETA_USER", {"email": "user@example.com"}, "admin@company.com")
log_admin_action("REMOVE_BETA_USER", {"email": "user@example.com"}, "admin@company.com")
log_admin_action("VIEW_USER_DATA", {"email": "user@example.com"}, "admin@company.com")
log_admin_action("EXPORT_REPORT", {"report_type": "usage", "date_range": "30_days"}, "admin@company.com")
```

This admin guide provides comprehensive coverage of all beta management features and best practices for administering the LLM Context Exporter beta program.