# Deployment Guide

## Overview

The Underwriting Agent is designed to be easily deployed to various environments.

## Local Development (Docker Compose)

See the main README for quick start with Docker Compose.

## Production Deployment

### Prerequisites

- Kubernetes 1.20+
- Docker registry (DockerHub, ECR, etc.)
- PostgreSQL 15+ (managed or self-hosted)
- Redis 7+ (managed or self-hosted)
- LLM API keys (OpenAI, Gemini, etc.)

### Environment Variables

Create a `.env` file with production settings:

```env
# Production settings
DEBUG=False
LOG_LEVEL=INFO

# Database - use RDS or managed PostgreSQL
DATABASE_URL=postgresql://user:pass@prod-db.rds.amazonaws.com:5432/underwriting

# Redis - use ElastiCache or managed Redis
REDIS_URL=redis://prod-redis.elasticache.amazonaws.com:6379

# LLM APIs
OPENAI_API_KEY=sk-prod-key
GEMINI_API_KEY=prod-key

# Security
SECRET_KEY=<generate-random-secret>
ALGORITHM=HS256

# API
API_WORKERS=8  # Increase for production
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=600

# Feature Management
ENABLE_ROUTER=true
ROUTER_COST_OPTIMIZATION=true
DEFAULT_MODEL_THRESHOLD=0.65

# Bandit
BANDIT_ALGORITHM=linucb
BANDIT_EXPLORATION_RATE=0.05  # Lower in production
```

### Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: underwriting-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: underwriting-api
  template:
    metadata:
      labels:
        app: underwriting-api
    spec:
      containers:
      - name: api
        image: your-registry/underwriting-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: underwriting-secrets
              key: database_url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: underwriting-secrets
              key: redis_url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: underwriting-api-service
spec:
  type: LoadBalancer
  selector:
    app: underwriting-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

### Running on AWS ECS

```bash
# Create ECR repository
aws ecr create-repository --repository-name underwriting-api

# Build and push image
docker build -t underwriting-api:latest backend/
docker tag underwriting-api:latest <account-id>.dkr.ecr.<region>.amazonaws.com/underwriting-api:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/underwriting-api:latest

# Create RDS database
aws rds create-db-instance \
  --db-instance-identifier underwriting-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password <strong-password>

# Create ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id underwriting-redis \
  --cache-node-type cache.t3.micro \
  --engine redis
```

### Running on Google Cloud

```bash
# Create Cloud Run services
gcloud run deploy underwriting-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Create Cloud SQL PostgreSQL
gcloud sql instances create underwriting-db \
  --database-version POSTGRES_15 \
  --tier db-f1-micro \
  --region us-central1

# Create Memorystore Redis
gcloud redis instances create underwriting-redis \
  --size 1 \
  --region us-central1
```

### Running on Azure

```bash
# Create PostgreSQL
az postgres server create \
  --resource-group myResourceGroup \
  --name underwriting-db \
  --location eastus \
  --admin-user admin \
  --admin-password <password>

# Create App Service
az appservice plan create \
  --name underwriting-plan \
  --resource-group myResourceGroup

az webapp create \
  --resource-group myResourceGroup \
  --plan underwriting-plan \
  --name underwriting-api \
  --deployment-container-image-name underwriting-api:latest
```

## Database Migrations

Use Alembic for migrations (scaffolding included):

```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Monitoring

### Application Metrics

Use Prometheus + Grafana:

```python
# In main.py, add Prometheus instrumentation
from prometheus_client import Counter, Histogram, generate_latest

decision_counter = Counter('underwriting_decisions_total', 'Total decisions')
decision_latency = Histogram('underwriting_decision_latency_ms', 'Decision latency')
```

### Logging

Configure centralized logging:

```python
# CloudWatch (AWS)
import watchtower
logging.getLogger().addHandler(
    watchtower.CloudWatchLogHandler()
)

# Stackdriver (GCP)
import google.cloud.logging
logging_client = google.cloud.logging.Client()
logging_client.setup_logging()
```

### Alerts

Set up alerts for:
- High error rate (>1%)
- Latency p99 > 5s
- Database connection issues
- API response time degradation
- Bandit algorithm not converging

## Security Checklist

- [ ] HTTPS/TLS enabled
- [ ] Database credentials in secrets manager
- [ ] API key rotation enabled
- [ ] Rate limiting configured
- [ ] CORS properly restricted
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (using ORM)
- [ ] CSRF protection if needed
- [ ] Regular security audits
- [ ] Incident response plan

## Performance Optimization

### Database
- Enable connection pooling (20 connections)
- Create indexes on frequently queried columns
- Archive old decisions (>1 year) to separate table
- Use read replicas for analytics queries

### Caching
- Cache features for 1 hour (default)
- Cache routing decisions for 30 minutes
- Cache model metrics for 5 minutes

### API
- Enable gzip compression
- Use CDN for static assets
- Enable HTTP caching headers
- Implement rate limiting

### LLM Calls
- Cache LLM responses for identical prompts
- Use faster models by default, upgrade when needed
- Batch requests when possible
- Implement timeouts (60s default)

## Cost Optimization

### LLM Cost Reduction
- Route 60% to cheap models (GPT-3.5)
- Route 30% to medium models (Gemini)
- Route 10% to expensive models (GPT-4)
- Skip LLM for 20% of high-confidence cases

Target cost: $0.005 per decision

### Infrastructure Cost Reduction
- Use spot instances for non-critical services
- Right-size database (t3.micro for <1000 decisions/day)
- Archive historical data automatically
- Use managed services (RDS, ElastiCache) to reduce ops

## Scalability Plan

### Phase 1 (0-100 decisions/day)
- Single API server
- Shared PostgreSQL + Redis

### Phase 2 (100-10k decisions/day)
- 2-3 API servers behind load balancer
- Separate database (RDS)
- Managed Redis (ElastiCache)

### Phase 3 (10k-100k decisions/day)
- 5-10 API servers
- Read replicas for PostgreSQL
- Sharding for analytics queries
- Separate read/write databases

### Phase 4 (100k+ decisions/day)
- Kubernetes auto-scaling
- Database cluster with read replicas
- Event streaming (Kafka) for audit trail
- Separate analytics database (Data Warehouse)

## Disaster Recovery

### Backup Strategy
- Daily automated PostgreSQL backups to S3
- Redis persistence enabled (RDB + AOF)
- Document versioning in RAG storage
- Regular restoration testing

### High Availability
- Multi-region deployment
- Database failover enabled
- Secrets manager for sensitive credentials
- Health checks on all services

### RTO/RPO Targets
- Recovery Time Objective: 1 hour
- Recovery Point Objective: 15 minutes
