# Production Deployment Checklist

This checklist ensures all critical components are properly configured before deploying LLM Context Exporter to production.

## Pre-Deployment Setup

### 1. Environment Configuration
- [ ] Copy `config/production.env.example` to `config/production.env`
- [ ] Generate secure `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Set strong `POSTGRES_PASSWORD` and `REDIS_PASSWORD`
- [ ] Configure domain name in `DOMAIN_NAME`
- [ ] Set admin email in `EMAIL_FOR_SSL`
- [ ] Verify `ENFORCE_HTTPS=true` for production

### 2. Stripe Configuration
- [ ] Obtain Stripe production API keys
- [ ] Set `STRIPE_PUBLISHABLE_KEY` (pk_live_...)
- [ ] Set `STRIPE_SECRET_KEY` (sk_live_...)
- [ ] Create product and price in Stripe dashboard
- [ ] Set `STRIPE_PRICE_ID` from Stripe dashboard
- [ ] Configure webhook endpoint in Stripe dashboard
- [ ] Set `STRIPE_WEBHOOK_SECRET` from webhook configuration

### 3. Email Configuration (Optional but Recommended)
- [ ] Configure SMTP server settings
- [ ] Set `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- [ ] Set `FROM_EMAIL` for system notifications
- [ ] Test email delivery

### 4. Backup Configuration (Optional)
- [ ] Create AWS S3 bucket for backups
- [ ] Set `BACKUP_S3_BUCKET` name
- [ ] Configure AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- [ ] Set `AWS_REGION`
- [ ] Enable backups with `BACKUP_ENABLED=true`

### 5. DNS and Domain Setup
- [ ] Purchase and configure domain name
- [ ] Point domain A record to server IP address
- [ ] Verify DNS propagation (`dig your-domain.com`)
- [ ] Ensure port 80 and 443 are open on server

## Deployment Process

### 1. Server Preparation
- [ ] Install Docker and Docker Compose
- [ ] Clone repository to server
- [ ] Set up production environment file
- [ ] Run deployment script: `./deployment/scripts/deploy.sh`

### 2. SSL Certificate Setup
- [ ] Run SSL setup: `./deployment/scripts/ssl_setup.sh`
- [ ] Verify certificate installation
- [ ] Test HTTPS access
- [ ] Set up auto-renewal cron job

### 3. Application Deployment
- [ ] Build and start all services
- [ ] Verify all containers are running
- [ ] Check application logs for errors
- [ ] Test health endpoint: `curl https://your-domain.com/health`

### 4. Database Setup
- [ ] Verify PostgreSQL is running
- [ ] Check database connectivity
- [ ] Run any required migrations
- [ ] Set up database backup schedule

## Post-Deployment Verification

### 1. Functional Testing
- [ ] Run end-to-end tests: `./deployment/scripts/e2e_test.sh`
- [ ] Test file upload functionality
- [ ] Verify payment processing (test mode first)
- [ ] Test beta user functionality
- [ ] Verify email notifications work

### 2. Security Testing
- [ ] Verify HTTPS redirect works
- [ ] Check security headers are present
- [ ] Test rate limiting functionality
- [ ] Verify CORS configuration
- [ ] Test API authentication

### 3. Performance Testing
- [ ] Load test with multiple concurrent uploads
- [ ] Monitor memory and CPU usage
- [ ] Test large file uploads (up to 500MB)
- [ ] Verify response times are acceptable

### 4. Monitoring Setup
- [ ] Access Prometheus at `https://your-domain.com:9090`
- [ ] Access Grafana at `https://your-domain.com:3000`
- [ ] Configure Grafana admin password
- [ ] Import dashboard configuration
- [ ] Set up alert notifications

## Ongoing Maintenance

### 1. Backup Verification
- [ ] Test backup script: `./deployment/scripts/backup.sh`
- [ ] Verify backups are created successfully
- [ ] Test backup restoration process
- [ ] Monitor backup storage usage

### 2. Health Monitoring
- [ ] Set up automated health checks
- [ ] Configure alert notifications
- [ ] Monitor application metrics
- [ ] Review logs regularly

### 3. Security Updates
- [ ] Set up automatic security updates for OS
- [ ] Monitor Docker image updates
- [ ] Review and update SSL certificates
- [ ] Regular security audits

### 4. Performance Optimization
- [ ] Monitor resource usage trends
- [ ] Optimize database queries if needed
- [ ] Scale services based on usage
- [ ] Review and adjust rate limits

## Troubleshooting

### Common Issues
1. **SSL Certificate Issues**
   - Verify DNS is pointing to correct server
   - Check port 80 is accessible
   - Run: `./deployment/scripts/ssl_setup.sh check`

2. **Database Connection Issues**
   - Check PostgreSQL container status
   - Verify environment variables
   - Run: `./deployment/scripts/health_check.sh database`

3. **Payment Processing Issues**
   - Verify Stripe keys are correct
   - Check webhook configuration
   - Test with Stripe test keys first

4. **High Memory Usage**
   - Monitor Grafana dashboard
   - Check for memory leaks in logs
   - Consider scaling up server resources

### Emergency Procedures
1. **Service Outage**
   ```bash
   # Check service status
   ./deployment/scripts/health_check.sh
   
   # Restart services
   cd deployment/docker
   docker-compose -f docker-compose.prod.yml restart
   ```

2. **Database Issues**
   ```bash
   # Restore from backup
   ./deployment/scripts/backup.sh restore
   
   # Check database integrity
   docker exec llm-context-postgres pg_dump --schema-only
   ```

3. **SSL Certificate Expiry**
   ```bash
   # Renew certificate
   ./deployment/scripts/ssl_setup.sh renew
   ```

## Contact Information

- **System Administrator**: [Your Email]
- **Emergency Contact**: [Emergency Phone]
- **Hosting Provider**: [Provider Support]
- **Domain Registrar**: [Registrar Support]

## Deployment Sign-off

- [ ] All checklist items completed
- [ ] End-to-end tests passing
- [ ] Monitoring configured and working
- [ ] Backup system tested
- [ ] Documentation updated
- [ ] Team notified of deployment

**Deployed by**: ________________  
**Date**: ________________  
**Version**: ________________  
**Notes**: ________________