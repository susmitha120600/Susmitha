# Deployment Guide

This guide covers deploying the Agentic AI Ecosystem to production environments.

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Monitoring & Logging](#monitoring--logging)
6. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites
- Python 3.10+
- PostgreSQL 15+
- Redis 7+
- OpenAI API Key

### Setup Steps

1. **Clone and setup environment**
```bash
git clone <repository-url>
cd AgenticAI-Ecosystem
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Initialize database**
```bash
python scripts/init_db.py
```

4. **Run the application**
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Access the API**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

---

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Build and start services**
```bash
docker-compose up -d --build
```

2. **View logs**
```bash
docker-compose logs -f api
```

3. **Stop services**
```bash
docker-compose down
```

4. **Stop and remove volumes**
```bash
docker-compose down -v
```

### Services Included
- **api**: Main FastAPI application (port 8000)
- **postgres**: PostgreSQL database (port 5432)
- **redis**: Redis cache (port 6379)
- **pgadmin**: Database admin UI (port 5050)

### Scaling

Scale the API service:
```bash
docker-compose up -d --scale api=3
```

Add load balancer (nginx):
```yaml
# Add to docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
  depends_on:
    - api
```

---

## Cloud Deployment

### AWS Deployment (ECS/Fargate)

1. **Build and push Docker image**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t agenticai-ecosystem .
docker tag agenticai-ecosystem:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/agenticai-ecosystem:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/agenticai-ecosystem:latest
```

2. **Create ECS Task Definition**
```json
{
  "family": "agenticai-ecosystem",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/agenticai-ecosystem:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:..."
        }
      ]
    }
  ]
}
```

3. **Deploy with Terraform** (optional)
```hcl
resource "aws_ecs_service" "agenticai" {
  name            = "agenticai-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.agenticai.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets         = var.private_subnets
    security_groups = [aws_security_group.agenticai.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.agenticai.arn
    container_name   = "api"
    container_port   = 8000
  }
}
```

### Google Cloud Platform (Cloud Run)

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/agenticai-ecosystem

gcloud run deploy agenticai-ecosystem \
  --image gcr.io/PROJECT_ID/agenticai-ecosystem \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=... \
  --set-secrets OPENAI_API_KEY=...
```

### Azure (Container Instances)

```bash
az container create \
  --resource-group agenticai-rg \
  --name agenticai-ecosystem \
  --image <registry>.azurecr.io/agenticai-ecosystem:latest \
  --dns-name-label agenticai \
  --ports 8000 \
  --environment-variables DATABASE_URL=... \
  --secure-environment-variables OPENAI_API_KEY=...
```

---

## Environment Configuration

### Production Environment Variables

```bash
# LLM Configuration
OPENAI_API_KEY=sk-prod-...
MODEL_NAME=gpt-4o
TEMPERATURE=0.1

# Database (Use managed services in production)
DATABASE_URL=postgresql://user:pass@prod-db.region.rds.amazonaws.com:5432/agenticai
REDIS_URL=redis://prod-redis.region.cache.amazonaws.com:6379/0

# Vector Database
VECTOR_DB_TYPE=pinecone  # Use Pinecone for production
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=agenticai-prod

# Security
SECRET_KEY=<generate-strong-random-key>
ALGORITHM=HS256

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_METRICS=true

# API
API_WORKERS=4
CORS_ORIGINS=["https://yourdomain.com"]
```

### Generate Secret Key
```python
import secrets
print(secrets.token_urlsafe(32))
```

---

## Monitoring & Logging

### Application Metrics

The application exposes metrics at `/metrics` (if enabled):
- Request count
- Response time
- Error rate
- Agent iterations
- Hallucination rate

### CloudWatch (AWS)
```python
# Add to requirements.txt
watchtower==3.0.1

# Configure in src/core/logging.py
import watchtower
logger.add(
    watchtower.CloudWatchLogHandler(),
    format="{message}",
    level="INFO"
)
```

### Prometheus + Grafana

```yaml
# docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Health Checks

```bash
# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /ping
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

# Readiness probe
readinessProbe:
  httpGet:
    path: /api/v1/health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check database connectivity
psql $DATABASE_URL -c "SELECT 1"

# Verify credentials
echo $DATABASE_URL
```

**2. Vector Index Not Found**
```bash
# Rebuild index
python scripts/ingest_documents.py --path ./data/documents
```

**3. High Memory Usage**
```bash
# Monitor container memory
docker stats agenticai-api

# Adjust in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

**4. Slow Response Times**
```bash
# Check logs for bottlenecks
docker-compose logs -f api | grep "Process-Time"

# Enable caching
REDIS_TTL=3600
```

### Performance Tuning

**1. Database Connection Pooling**
```python
# In .env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

**2. Async Workers**
```bash
# Increase Uvicorn workers
uvicorn src.api.main:app --workers 4 --host 0.0.0.0 --port 8000
```

**3. Caching Strategy**
```python
# Enable Redis caching for embeddings and LLM responses
REDIS_TTL=3600
```

### Logs Location

- **Local**: `./logs/app.log`
- **Docker**: `docker-compose logs -f api`
- **Production**: CloudWatch/Stackdriver/Azure Monitor

---

## Security Best Practices

1. **Never commit `.env` files**
2. **Use secrets management** (AWS Secrets Manager, Azure Key Vault)
3. **Enable HTTPS** in production
4. **Implement rate limiting**
5. **Regular security updates**
6. **Monitor API usage**
7. **Implement authentication** for production APIs

---

## Backup & Recovery

### Database Backup
```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20240101.sql
```

### Vector Index Backup
```bash
# Backup FAISS index
tar -czf vectorstore_backup.tar.gz ./data/vectorstore/

# Restore
tar -xzf vectorstore_backup.tar.gz -C ./data/
```

---

For additional support, refer to the main README.md or open an issue on GitHub.
