# LLM Context Exporter Deployment Guide

This guide provides step-by-step instructions for deploying the LLM Context Exporter to production.

## Deployment Options

### Option 1: Docker Compose (Recommended for Small-Medium Scale)
- **Pros**: Simple setup, includes all services, easy to manage
- **Cons**: Single server, limited scalability
- **Best for**: MVP, small teams, proof of concept

### Option 2: Render.com (Easiest Cloud Deployment)
- **Pros**: Managed infrastructure, automatic scaling, built-in SSL
- **Cons**: Less control, vendor lock-in, higher cost at scale
- **Best for**: Quick deployment, teams without DevOps expertise

### Option 3: AWS/GCP/Azure (Enterprise Scale)
- **Pros**: Full control, unlimited scalability, enterprise features
- **Cons**: Complex setup, requires DevOps expertise
- **Best for**: Large scale, enterprise deployments

## Quick Start (Docker Compose)

### Prerequisites
- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Domain name pointing to your server
- Ports 80 and 443 open

### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply Docker group membership
```

### 2. Application Setup
```bash
# Clone repository
git clone https://github.com/your-org/llm-context-exporter.git
cd llm-context-exporter

# Copy environment template
cp deployment/config/production.env.example deployment/config/production.env

# Edit configuration (see Configuration section below)
nano deployment/config/production.env
```

### 3. Configuration
Edit `deployment/config/production.env` with your settings:

```bash
# Required Settings
SECRET_KEY=your-super-secret-key-change-this-in-production
POSTGRES_PASSWORD=your-secure-database-password
REDIS_PASSWORD=your-secure-redis-password
DOMAIN_NAME=your-domain.com
EMAIL_FOR_SSL=admin@your-domain.com

# Stripe Configuration (Production Keys)
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PRICE_ID=price_your_price_id

# Optional: Email Configuration
SMTP_SERVER=smtp.your-email-provider.com
SMTP_USERNAME=your-email@your-domain.com
SMTP_PASSWORD=your-email-password
FROM_EMAIL=noreply@your-domain.com

# Optional: Backup Configuration
BACKUP_ENABLED=true
BACKUP_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
```

### 4. Deploy
```bash
# Run deployment script
./deployment/scripts/deploy.sh

# The script will:
# - Validate configuration
# - Set up SSL certificates
# - Build and start all services
# - Configure monitoring
# - Set up backups
# - Run health checks
```

### 5. Verify Deployment
```bash
# Run end-to-end tests
./deployment/scripts/e2e_test.sh

# Check service status
./deployment/scripts/health_check.sh

# View logs
cd deployment/docker
docker-compose -f docker-compose.prod.yml logs -f
```

## Render.com Deployment

### 1. Prepare Repository
```bash
# Ensure render.yaml is in repository root
cp llm-context-exporter/render.yaml ./render.yaml

# Commit and push to GitHub
git add render.yaml
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Create Render Account
1. Sign up at [render.com](https://render.com)
2. Connect your GitHub account
3. Select your repository

### 3. Configure Services
1. **Web Service**:
   - Name: `llm-context-exporter`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt && pip install -e .`
   - Start Command: `gunicorn --config deployment/config/gunicorn.conf.py llm_context_exporter.web.app:create_app()`

2. **PostgreSQL Database**:
   - Name: `llm-context-postgres`
   - Plan: Starter (upgrade for production)

3. **Redis Cache**:
   - Name: `llm-context-redis`
   - Plan: Starter (upgrade for production)

### 4. Environment Variables
Set these in the Render dashboard:
- `SECRET_KEY`: Generate secure key
- `STRIPE_PUBLISHABLE_KEY`: Your Stripe publishable key
- `STRIPE_SECRET_KEY`: Your Stripe secret key
- `STRIPE_WEBHOOK_SECRET`: From Stripe webhook configuration
- `STRIPE_PRICE_ID`: From Stripe product configuration

### 5. Custom Domain (Optional)
1. Add custom domain in Render dashboard
2. Update DNS records as instructed
3. SSL certificate will be automatically provisioned

## AWS Deployment (Advanced)

### Prerequisites
- AWS CLI configured
- Terraform installed (optional)
- kubectl installed (for EKS)

### 1. Infrastructure Setup
```bash
# Using Terraform (recommended)
cd deployment/terraform
terraform init
terraform plan
terraform apply

# Or using AWS CLI
aws cloudformation create-stack \
  --stack-name llm-context-exporter \
  --template-body file://cloudformation.yaml \
  --parameters ParameterKey=DomainName,ParameterValue=your-domain.com
```

### 2. Container Registry
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

docker build -f deployment/docker/Dockerfile.prod -t llm-context-exporter .
docker tag llm-context-exporter:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-context-exporter:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-context-exporter:latest
```

### 3. Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f deployment/k8s/

# Check deployment status
kubectl get pods -n llm-context-exporter
kubectl get services -n llm-context-exporter
```

## Configuration Details

### Stripe Setup
1. **Create Stripe Account**: Sign up at [stripe.com](https://stripe.com)
2. **Create Product**: 
   - Go to Products in Stripe Dashboard
   - Create new product: "LLM Context Export"
   - Set price (e.g., $5.00 one-time)
   - Copy the Price ID
3. **Get API Keys**:
   - Go to Developers > API Keys
   - Copy Publishable Key (pk_live_...)
   - Copy Secret Key (sk_live_...)
4. **Configure Webhook**:
   - Go to Developers > Webhooks
   - Add endpoint: `https://your-domain.com/api/payment/webhook`
   - Select events: `payment_intent.succeeded`, `payment_intent.payment_failed`
   - Copy webhook secret

### Email Configuration
For system notifications and receipts:
```bash
# Gmail SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use app password, not regular password

# SendGrid SMTP
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

### Backup Configuration
For automated backups to AWS S3:
```bash
# Create S3 bucket
aws s3 mb s3://your-backup-bucket

# Create IAM user with S3 access
aws iam create-user --user-name llm-context-backup
aws iam attach-user-policy --user-name llm-context-backup --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam create-access-key --user-name llm-context-backup
```

## Monitoring and Maintenance

### Accessing Monitoring
- **Prometheus**: `https://your-domain.com:9090`
- **Grafana**: `https://your-domain.com:3000`
  - Default login: admin / (check GRAFANA_PASSWORD in config)

### Regular Maintenance Tasks
```bash
# Weekly health check
./deployment/scripts/health_check.sh

# Manual backup
./deployment/scripts/backup.sh

# SSL certificate renewal (automated via cron)
./deployment/scripts/ssl_setup.sh renew

# Update application
git pull origin main
cd deployment/docker
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Log Management
```bash
# View application logs
docker-compose -f deployment/docker/docker-compose.prod.yml logs -f app

# View specific service logs
docker-compose -f deployment/docker/docker-compose.prod.yml logs -f postgres
docker-compose -f deployment/docker/docker-compose.prod.yml logs -f redis

# Log rotation is handled automatically by Docker
```

## Scaling and Performance

### Vertical Scaling (Single Server)
```bash
# Increase server resources
# Update docker-compose.prod.yml with resource limits
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Horizontal Scaling (Multiple Servers)
For high-traffic deployments:
1. Use load balancer (AWS ALB, Nginx, Cloudflare)
2. Separate database to managed service (AWS RDS, Google Cloud SQL)
3. Use Redis cluster for session storage
4. Implement container orchestration (Kubernetes, Docker Swarm)

### Performance Optimization
```bash
# Monitor performance
./deployment/scripts/health_check.sh

# Optimize database
docker exec llm-context-postgres psql -U llm_user -d llm_context_exporter -c "VACUUM ANALYZE;"

# Clear Redis cache if needed
docker exec llm-context-redis redis-cli -a $REDIS_PASSWORD FLUSHALL
```

## Security Best Practices

### 1. Server Security
```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

### 2. Application Security
- Use strong passwords for all services
- Enable HTTPS in production (`ENFORCE_HTTPS=true`)
- Regularly update Docker images
- Monitor security alerts
- Use secrets management for sensitive data

### 3. Database Security
- Use strong database passwords
- Enable SSL for database connections
- Regular security updates
- Backup encryption

## Troubleshooting

### Common Issues

1. **SSL Certificate Issues**
```bash
# Check certificate status
./deployment/scripts/ssl_setup.sh check

# Renew certificate
./deployment/scripts/ssl_setup.sh renew

# Check DNS
dig your-domain.com
```

2. **Database Connection Issues**
```bash
# Check database status
docker-compose -f deployment/docker/docker-compose.prod.yml ps postgres

# Check database logs
docker-compose -f deployment/docker/docker-compose.prod.yml logs postgres

# Test connection
docker exec llm-context-postgres pg_isready -U llm_user -d llm_context_exporter
```

3. **Payment Processing Issues**
```bash
# Test Stripe connectivity
curl -u sk_test_...: https://api.stripe.com/v1/charges

# Check webhook configuration
# Verify webhook URL in Stripe dashboard
# Check webhook secret matches configuration
```

4. **High Memory Usage**
```bash
# Check memory usage
free -h
docker stats

# Restart services if needed
docker-compose -f deployment/docker/docker-compose.prod.yml restart
```

### Getting Help
- Check application logs first
- Run health check script
- Review monitoring dashboards
- Check GitHub issues
- Contact support team

## Rollback Procedures

### Application Rollback
```bash
# Rollback to previous version
git checkout previous-tag
docker-compose -f deployment/docker/docker-compose.prod.yml build --no-cache
docker-compose -f deployment/docker/docker-compose.prod.yml up -d
```

### Database Rollback
```bash
# Restore from backup
./deployment/scripts/backup.sh restore backup_file.sql.gz
```

### Configuration Rollback
```bash
# Restore previous configuration
cp deployment/config/production.env.backup deployment/config/production.env
docker-compose -f deployment/docker/docker-compose.prod.yml restart
```