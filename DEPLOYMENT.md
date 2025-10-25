# Deployment Guide

This guide covers deployment strategies for the Replo application across different platforms and environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [AWS Deployment](#aws-deployment)
4. [Vercel Deployment](#vercel-deployment)
5. [Generic Hosting](#generic-hosting)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- Docker & Docker Compose
- AWS CLI (for AWS deployments)
- kubectl (for Kubernetes deployments)
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Environment Setup
1. Copy `.env.example` to `.env` and configure all variables
2. Ensure all secrets are properly set
3. Configure domain names and SSL certificates

## Local Development

### Database-Only Development
For development where frontend and backend run locally:

```bash
# Start only database services
docker compose -f docker-compose.dev.yml up -d

# Optional: Start with admin tools
docker compose -f docker-compose.dev.yml --profile admin up -d

# Run backend locally
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend locally (in another terminal)
cd frontend/replo
npm install
npm run dev
```

### Full Docker Development
```bash
# Start all services with live reload
docker compose up --no-build backend frontend

# View logs
docker compose logs -f backend frontend
```

## AWS Deployment

### Option 1: AWS ECS (Recommended for simplicity)

#### Prerequisites
- AWS CLI configured with appropriate permissions
- ECR repositories created for frontend and backend images
- ECS cluster created
- Application Load Balancer configured
- RDS PostgreSQL instance
- ElastiCache Redis cluster

#### Step 1: Build and Push Images
```bash
# Build images
docker build -f backend/Dockerfile -t replo/backend:latest backend/
docker build -f frontend/replo/Dockerfile -t replo/frontend:latest frontend/replo/

# Tag for ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-west-2.amazonaws.com

docker tag replo/backend:latest <account-id>.dkr.ecr.us-west-2.amazonaws.com/replo/backend:latest
docker tag replo/frontend:latest <account-id>.dkr.ecr.us-west-2.amazonaws.com/replo/frontend:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/replo/backend:latest
docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/replo/frontend:latest
```

#### Step 2: ECS Task Definitions
Create task definitions for each service:

**Backend Task Definition:**
```json
{
  "family": "replo-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-west-2.amazonaws.com/replo/backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:<account-id>:secret:replo/database-url"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:<account-id>:secret:replo/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/replo-backend",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### Step 3: ECS Services
Create ECS services with auto-scaling and load balancer integration.

#### Step 4: Infrastructure as Code (Optional)
Use AWS CDK or Terraform for infrastructure management:

```typescript
// AWS CDK example
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

const cluster = new ecs.Cluster(this, 'ReplogCluster', {
  vpc: vpc,
  containerInsights: true
});

const backendService = new ecs.FargateService(this, 'BackendService', {
  cluster,
  taskDefinition: backendTaskDef,
  desiredCount: 2,
  assignPublicIp: false,
  securityGroups: [backendSecurityGroup]
});
```

### Option 2: AWS EKS (For advanced Kubernetes needs)

#### Prerequisites
- EKS cluster created
- kubectl configured for EKS
- Helm installed
- AWS Load Balancer Controller installed

#### Step 1: Kubernetes Manifests
Create Kubernetes deployment files:

**backend-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: replo-backend
  namespace: replo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: replo-backend
  template:
    metadata:
      labels:
        app: replo-backend
    spec:
      containers:
      - name: backend
        image: <account-id>.dkr.ecr.us-west-2.amazonaws.com/replo/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: replo-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: replo-secrets
              key: openai-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: replo-backend-service
  namespace: replo
spec:
  selector:
    app: replo-backend
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Step 2: Deploy to EKS
```bash
# Create namespace
kubectl create namespace replo

# Create secrets
kubectl create secret generic replo-secrets \
  --from-literal=database-url="postgresql://user:pass@host:5432/db" \
  --from-literal=openai-key="your-openai-key" \
  -n replo

# Deploy applications
kubectl apply -f k8s/ -n replo

# Create ingress
kubectl apply -f ingress.yaml -n replo
```

## Vercel Deployment

### Frontend-Only Deployment (Recommended)
Deploy only the frontend to Vercel while keeping the backend on AWS/other providers.

#### Step 1: Vercel Configuration
Create `vercel.json` in the frontend directory:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://api.yourdomain.com"
  },
  "functions": {
    "app/api/**/*.js": {
      "maxDuration": 30
    }
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.yourdomain.com/:path*"
    }
  ]
}
```

#### Step 2: Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from frontend directory
cd frontend/replo
vercel --prod

# Set environment variables
vercel env add NEXT_PUBLIC_API_URL production
```

#### Step 3: Custom Domain & SSL
Configure custom domain and SSL through Vercel dashboard.

### Full-Stack Vercel Deployment (Limited)
For smaller applications, you can deploy the backend as Vercel functions:

```javascript
// api/backend/[...slug].js
export default async function handler(req, res) {
  // Proxy to your FastAPI application
  // Note: This has limitations for complex backends
}
```

## Generic Hosting

### VPS/Dedicated Server Deployment

#### Prerequisites
- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Nginx for reverse proxy
- SSL certificates (Let's Encrypt recommended)

#### Step 1: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo apt install nginx -y

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

#### Step 2: Nginx Configuration
Create `/etc/nginx/sites-available/replo`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "https://yourdomain.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
}
```

#### Step 3: SSL Certificate
```bash
# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

#### Step 4: Deploy Application
```bash
# Clone repository
git clone https://github.com/your-org/replo.git
cd replo

# Configure environment
cp .env.example .env
# Edit .env with production values

# Build and start services
docker compose -f docker-compose.prod.yml up -d

# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/replo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Digital Ocean App Platform

#### Step 1: App Spec Configuration
Create `.do/app.yaml`:

```yaml
name: replo
services:
- name: backend
  source_dir: backend
  github:
    repo: your-org/replo
    branch: main
  run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
  environment_slug: python
  instance_count: 2
  instance_size_slug: basic-xxs
  http_port: 8080
  health_check:
    http_path: /health
  envs:
  - key: ENVIRONMENT
    value: production
  - key: DATABASE_URL
    type: SECRET
  - key: OPENAI_API_KEY
    type: SECRET

- name: frontend
  source_dir: frontend/replo
  github:
    repo: your-org/replo
    branch: main
  run_command: npm start
  environment_slug: node-js
  instance_count: 2
  instance_size_slug: basic-xxs
  http_port: 3000
  envs:
  - key: NEXT_PUBLIC_API_URL
    value: ${backend.PUBLIC_URL}

databases:
- name: postgres
  engine: PG
  version: "15"
  size: basic-xs
  num_nodes: 1

- name: redis
  engine: REDIS
  version: "7"
  size: basic-xs
  num_nodes: 1
```

#### Step 2: Deploy
```bash
# Install doctl
# Configure doctl auth

# Deploy
doctl apps create --spec .do/app.yaml
```

## Monitoring & Maintenance

### Health Checks
All services include health check endpoints:
- Frontend: `GET /api/health`
- Backend: `GET /health`
- Database: Built-in PostgreSQL health checks
- Redis: Built-in Redis health checks

### Logging
- Application logs: Structured JSON logging
- Access logs: Nginx/Load Balancer logs
- Error tracking: Sentry integration (optional)

### Monitoring Stack (Optional)
Enable monitoring with Prometheus and Grafana:

```bash
# Start monitoring services
docker compose -f docker-compose.prod.yml --profile monitoring up -d

# Access Grafana at http://localhost:3001
# Access Prometheus at http://localhost:9090
```

### Backup Strategy
1. **Database Backups**: Automated daily backups to S3
2. **Application Data**: Version control for code
3. **Configuration**: Environment variables in secure storage

### Scaling Considerations

#### Horizontal Scaling
- **Frontend**: Stateless, can scale infinitely
- **Backend**: Stateless API, scale based on CPU/memory
- **Worker**: Scale based on queue length
- **Database**: Read replicas for read-heavy workloads

#### Resource Requirements

**Minimum Production Setup:**
- Frontend: 512MB RAM, 0.5 CPU
- Backend: 1GB RAM, 1 CPU
- Worker: 512MB RAM, 0.5 CPU
- Database: 2GB RAM, 1 CPU
- Redis: 256MB RAM, 0.25 CPU

**Recommended Production Setup:**
- Frontend: 1GB RAM, 1 CPU (2 replicas)
- Backend: 2GB RAM, 2 CPU (2 replicas)
- Worker: 1GB RAM, 1 CPU (1 replica)
- Database: 4GB RAM, 2 CPU
- Redis: 512MB RAM, 0.5 CPU

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check database connectivity
docker exec -it replo-postgres-prod psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"

# Check logs
docker logs replo-postgres-prod
```

#### 2. Redis Connection Issues
```bash
# Test Redis connectivity
docker exec -it replo-redis-prod redis-cli ping

# Check Redis logs
docker logs replo-redis-prod
```

#### 3. Application Startup Issues
```bash
# Check application logs
docker logs replo-backend-prod
docker logs replo-frontend-prod

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:3000/api/health
```

#### 4. SSL/TLS Issues
```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check certificate expiry
echo | openssl s_client -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Performance Optimization

#### 1. Database Optimization
- Enable connection pooling
- Optimize queries with EXPLAIN ANALYZE
- Set up read replicas for read-heavy workloads
- Regular VACUUM and ANALYZE

#### 2. Application Optimization
- Enable Redis caching
- Optimize Docker images (multi-stage builds)
- Use CDN for static assets
- Enable gzip compression

#### 3. Infrastructure Optimization
- Use load balancers for high availability
- Implement auto-scaling policies
- Monitor resource usage
- Set up alerting for critical metrics

### Security Best Practices

1. **Secrets Management**: Use AWS Secrets Manager, HashiCorp Vault, or similar
2. **Network Security**: Private subnets, security groups, VPC
3. **Container Security**: Non-root users, minimal base images
4. **SSL/TLS**: Strong ciphers, HSTS headers
5. **Access Control**: IAM roles, least privilege principle
6. **Monitoring**: Security logs, intrusion detection
7. **Updates**: Regular security updates, vulnerability scanning

### Disaster Recovery

1. **Backup Strategy**: Automated backups with point-in-time recovery
2. **Multi-Region**: Deploy across multiple availability zones
3. **Failover**: Automated failover for critical services
4. **Testing**: Regular disaster recovery testing
5. **Documentation**: Runbooks for incident response

For additional support or questions, refer to the project documentation or contact the development team.