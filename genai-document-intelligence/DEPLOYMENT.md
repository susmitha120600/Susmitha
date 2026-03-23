# Deployment Guide

## Local Deployment

### Prerequisites

1. **Python 3.9+** installed
2. **API Keys**:
   - OpenAI API key
   - Pinecone API key

### Step-by-Step Local Setup

#### 1. Clone and Navigate

```bash
cd genai-doc-intelligence
```

#### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

```bash
# Copy the example environment file
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux

# Edit .env and add your API keys
```

Required environment variables:
```env
OPENAI_API_KEY=your_openai_key_here
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=doc-intelligence
```

#### 5. Create Data Directories

```bash
mkdir -p data/documents data/evaluation
```

#### 6. Run the Application

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 7. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

---

## Docker Deployment

### Using Docker Compose (Recommended)

#### 1. Create .env File

```bash
cd docker
copy ..\.env.example ..\.env  # Windows
cp ../.env.example ../.env    # macOS/Linux
```

Edit `.env` with your API keys.

#### 2. Build and Run

```bash
docker-compose up --build
```

#### 3. Run in Background

```bash
docker-compose up -d
```

#### 4. View Logs

```bash
docker-compose logs -f api
```

#### 5. Stop Services

```bash
docker-compose down
```

### Using Docker Only

#### 1. Build Image

```bash
docker build -f docker/Dockerfile -t genai-doc-intelligence .
```

#### 2. Run Container

```bash
docker run -d \
  --name genai-api \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e PINECONE_API_KEY=your_key \
  -e PINECONE_ENVIRONMENT=us-east-1-aws \
  -v $(pwd)/data:/app/data \
  genai-doc-intelligence
```

---

## Cloud Deployment

### AWS Deployment (ECS/Fargate)

#### 1. Build and Push to ECR

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -f docker/Dockerfile -t genai-doc-intelligence .

# Tag image
docker tag genai-doc-intelligence:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/genai-doc-intelligence:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/genai-doc-intelligence:latest
```

#### 2. Create ECS Task Definition

```json
{
  "family": "genai-doc-intelligence",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/genai-doc-intelligence:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "PINECONE_ENVIRONMENT", "value": "us-east-1-aws"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account-id:secret:openai-key"
        },
        {
          "name": "PINECONE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account-id:secret:pinecone-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/genai-doc-intelligence",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 3. Create ECS Service

```bash
aws ecs create-service \
  --cluster genai-cluster \
  --service-name genai-doc-intelligence \
  --task-definition genai-doc-intelligence \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Google Cloud Platform (Cloud Run)

#### 1. Build and Push to GCR

```bash
# Build image
docker build -f docker/Dockerfile -t gcr.io/project-id/genai-doc-intelligence .

# Push to GCR
docker push gcr.io/project-id/genai-doc-intelligence
```

#### 2. Deploy to Cloud Run

```bash
gcloud run deploy genai-doc-intelligence \
  --image gcr.io/project-id/genai-doc-intelligence \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PINECONE_ENVIRONMENT=us-east-1-aws \
  --set-secrets OPENAI_API_KEY=openai-key:latest,PINECONE_API_KEY=pinecone-key:latest \
  --memory 4Gi \
  --cpu 2 \
  --port 8000
```

### Azure (Container Instances)

```bash
az container create \
  --resource-group genai-rg \
  --name genai-doc-intelligence \
  --image <registry>.azurecr.io/genai-doc-intelligence:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables \
    PINECONE_ENVIRONMENT=us-east-1-aws \
  --secure-environment-variables \
    OPENAI_API_KEY=your_key \
    PINECONE_API_KEY=your_key
```

---

## Production Considerations

### 1. Environment Variables

Store sensitive credentials in:
- **AWS**: Secrets Manager or Parameter Store
- **GCP**: Secret Manager
- **Azure**: Key Vault
- **Kubernetes**: Secrets

### 2. Scaling

#### Horizontal Scaling
```bash
# Docker Compose
docker-compose up --scale api=3

# Kubernetes
kubectl scale deployment genai-api --replicas=5
```

#### Auto-scaling (Kubernetes)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: genai-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: genai-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### 3. Monitoring

#### Prometheus + Grafana

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### 4. Load Balancing

#### Nginx Configuration

```nginx
upstream genai_backend {
    least_conn;
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://genai_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 5. SSL/TLS

```bash
# Using Certbot for Let's Encrypt
certbot --nginx -d api.example.com
```

### 6. Health Checks

Configure health checks in your load balancer:
- **Endpoint**: `/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Healthy threshold**: 2
- **Unhealthy threshold**: 3

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8000 | xargs kill -9
```

#### 2. Memory Issues
Increase Docker memory limit:
```bash
# Docker Desktop: Settings > Resources > Memory
# Or in docker-compose.yml:
services:
  api:
    mem_limit: 4g
```

#### 3. API Key Issues
Verify environment variables:
```bash
docker exec genai-api env | grep API_KEY
```

#### 4. Pinecone Connection Issues
Check network connectivity and API key validity.

---

## Performance Optimization

### 1. Enable Caching

Add Redis caching for embeddings and search results.

### 2. Batch Processing

Process multiple documents concurrently:
```python
# Use background tasks for ingestion
background_tasks.add_task(process_document, file_path)
```

### 3. Connection Pooling

Configure connection pools for database connections.

### 4. CDN

Use CDN for static assets and API responses where applicable.

---

## Backup and Recovery

### 1. Vector Store Backup

Regularly backup Pinecone index or export to local storage.

### 2. BM25 Index Backup

```bash
# Backup
cp data/bm25_index.pkl backups/bm25_index_$(date +%Y%m%d).pkl

# Restore
cp backups/bm25_index_20240101.pkl data/bm25_index.pkl
```

### 3. Configuration Backup

Version control all configuration files in Git.
