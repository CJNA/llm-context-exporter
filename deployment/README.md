# Deployment Guide

This directory contains all deployment configurations and scripts for the LLM Context Exporter.

## Directory Structure

```
deployment/
├── README.md                   # This file
├── docker/                     # Docker configurations
│   ├── Dockerfile.prod        # Production Docker image
│   ├── docker-compose.prod.yml # Production compose file
│   └── nginx.conf             # Nginx configuration
├── config/                     # Configuration files
│   ├── production.env.example # Production environment template
│   ├── gunicorn.conf.py       # Gunicorn configuration
│   └── logging.conf           # Logging configuration
├── scripts/                    # Deployment scripts
│   ├── deploy.sh              # Main deployment script
│   ├── backup.sh              # Database backup script
│   ├── health_check.sh        # Health check script
│   └── ssl_setup.sh           # SSL certificate setup
├── monitoring/                 # Monitoring configurations
│   ├── prometheus.yml         # Prometheus configuration
│   ├── grafana/               # Grafana dashboards
│   └── alerts.yml             # Alert rules
└── k8s/                       # Kubernetes manifests (optional)
    ├── deployment.yaml
    ├── service.yaml
    └── ingress.yaml
```

## Deployment Options

### Option 1: Docker Compose (Recommended for small-scale)
- Simple setup with Docker Compose
- Includes Nginx reverse proxy
- SSL termination with Let's Encrypt
- Automatic backups

### Option 2: Kubernetes (For larger scale)
- Scalable deployment
- Built-in load balancing
- Health checks and auto-recovery
- Rolling updates

### Option 3: Cloud Platforms
- Render.com (simple deployment)
- Heroku (easy setup)
- AWS/GCP/Azure (full control)

## Quick Start

1. Copy environment template:
   ```bash
   cp config/production.env.example config/production.env
   ```

2. Edit configuration:
   ```bash
   nano config/production.env
   ```

3. Run deployment:
   ```bash
   ./scripts/deploy.sh
   ```

## Security Considerations

- All secrets stored in environment variables
- HTTPS enforced in production
- Rate limiting enabled
- CORS restricted to specific origins
- Regular security updates

## Monitoring

- Health checks every 30 seconds
- Prometheus metrics collection
- Grafana dashboards for visualization
- Email alerts for critical issues

## Backup Strategy

- Daily database backups
- Encrypted backup storage
- 30-day retention policy
- Automated restore testing