# Deployment Guide: Triangulation Validator

**Version:** 0.1.0  
**Framework:** Spring Boot 3.2 + React 18  
**Status:** Production-Ready ✅

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Setup](#production-setup)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Minimum Requirements

**Development:**
- Java 21 (Eclipse Adoptium)
- Maven 3.9.16
- Node.js 18+
- PostgreSQL 13+ (or Docker)
- Docker & Docker Compose (optional but recommended)

**Production:**
- Docker & Docker Compose, OR
- Java 21 runtime
- PostgreSQL 13+
- Node.js 18+ (for frontend serving)
- 2GB RAM minimum
- 10GB disk space

### System Environment Variables

```bash
# Database
DATABASE_URL=jdbc:postgresql://localhost:5432/mycroft_triangulation
DB_USER=postgres
DB_PASSWORD=<secure_password>

# Agent Endpoints
AGENT_TALENT_URL=http://localhost:8081
AGENT_PATENT_URL=http://localhost:8082
AGENT_NEWS_URL=http://localhost:8083
AGENT_MARKET_URL=http://localhost:8084
AGENT_REGULATORY_URL=http://localhost:8085

# Application
SIGNAL_LOOKBACK_DAYS=7
JAVA_OPTS=-Xmx512m -Xms256m
SERVER_PORT=8080
```

---

## Local Development

### Quick Start with Docker Compose

```bash
# Clone the repository
git clone <repo> Mycroft
cd Mycroft/Core_Components/Triangulation_Validator

# Start all services
docker-compose up -d

# Verify services
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services Started:**
- PostgreSQL on `localhost:5432`
- Backend API on `localhost:8080`
- Frontend on `localhost:3000`
- Redis cache on `localhost:6379` (optional)

### Manual Local Setup

#### Backend

```bash
cd backend

# Create .env file
cp .env.example .env

# Edit .env with your database credentials
nano .env

# Install dependencies
mvn clean install

# Run tests
mvn test

# Start application
mvn spring-boot:run

# Application available at http://localhost:8080
# Swagger UI: http://localhost:8080/swagger-ui.html
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Frontend available at http://localhost:3000
```

---

## Docker Deployment

### Building Docker Image

```bash
# Build multi-stage image
docker build -t triangulation-validator:0.1.0 .

# Tag for registry
docker tag triangulation-validator:0.1.0 \
  <registry>/triangulation-validator:0.1.0

# Push to registry
docker push <registry>/triangulation-validator:0.1.0
```

### Running with Docker Compose

```bash
# Development environment
docker-compose up -d

# Production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale backend instances (with load balancer)
docker-compose up -d --scale backend=3
```

### Running Single Container

```bash
# Create network
docker network create triangulation

# Start PostgreSQL
docker run -d \
  --name db \
  --network triangulation \
  -e POSTGRES_DB=mycroft_triangulation \
  -e POSTGRES_PASSWORD=secure_password \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

# Start Triangulation Validator
docker run -d \
  --name triangulation \
  --network triangulation \
  -p 8080:8080 \
  -p 3000:3000 \
  -e DATABASE_URL=jdbc:postgresql://db:5432/mycroft_triangulation \
  -e DB_USER=postgres \
  -e DB_PASSWORD=secure_password \
  triangulation-validator:0.1.0
```

---

## Production Setup

### Kubernetes Deployment

#### Service Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: triangulation-validator
spec:
  selector:
    app: triangulation-validator
  ports:
    - protocol: TCP
      port: 8080
      targetPort: 8080
  type: LoadBalancer
```

#### Deployment Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: triangulation-validator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: triangulation-validator
  template:
    metadata:
      labels:
        app: triangulation-validator
    spec:
      containers:
      - name: triangulation
        image: <registry>/triangulation-validator:0.1.0
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: triangulation-secrets
              key: db-url
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: triangulation-secrets
              key: db-user
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: triangulation-secrets
              key: db-password
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Nginx Reverse Proxy

```nginx
upstream backend {
    server triangulation:8080;
}

upstream frontend {
    server triangulation:3000;
}

server {
    listen 80;
    server_name triangulation.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name triangulation.example.com;

    ssl_certificate /etc/ssl/certs/triangulation.crt;
    ssl_certificate_key /etc/ssl/private/triangulation.key;

    # API requests
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Backend health
curl http://localhost:8080/api/v1/health

# Database connectivity
curl http://localhost:8080/api/v1/health/db

# Agent availability
curl http://localhost:8080/api/v1/search/agents
```

### Logs

#### Docker
```bash
# Backend logs
docker-compose logs -f backend

# Database logs
docker-compose logs -f db

# All logs
docker-compose logs -f
```

#### Application Logs
```bash
# Backend logs location
backend/logs/triangulation-validator.log

# View logs
tail -f backend/logs/triangulation-validator.log
```

### Database Maintenance

```bash
# Backup database
pg_dump -U postgres -h localhost -d mycroft_triangulation > backup.sql

# Restore database
psql -U postgres -h localhost -d mycroft_triangulation < backup.sql

# Vacuum database (optimization)
psql -U postgres -h localhost -d mycroft_triangulation -c "VACUUM ANALYZE;"
```

### Performance Monitoring

```bash
# Monitor memory usage
docker stats triangulation

# Check disk usage
docker exec triangulation df -h

# Database query performance
docker exec db psql -U postgres -d mycroft_triangulation \
  -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Error:** `Connection refused: localhost:5432`

**Solution:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql -U postgres -h localhost -d mycroft_triangulation
```

#### 2. API Port Already in Use

**Error:** `Address already in use: 8080`

**Solution:**
```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or use different port
export SERVER_PORT=8081
```

#### 3. Frontend Cannot Connect to Backend

**Error:** `Failed to fetch from /api/`

**Solution:**
```bash
# Check backend is running
curl http://localhost:8080/api/v1/health

# Check CORS configuration
curl -H "Origin: http://localhost:3000" http://localhost:8080/api/v1/health

# Check proxy configuration in vite.config.ts
```

#### 4. Out of Memory

**Error:** `java.lang.OutOfMemoryError`

**Solution:**
```bash
# Increase heap size
export JAVA_OPTS="-Xmx1024m -Xms512m"

# Or in Docker
docker run -e JAVA_OPTS="-Xmx1024m" ...
```

### Debug Mode

```bash
# Enable debug logging
export LOGGING_LEVEL=DEBUG

# Spring Boot debug
export SPRING_BOOT_DEBUG=true

# Maven with debug
mvn -e -X spring-boot:run

# Node debug
NODE_DEBUG=* npm run dev
```

---

## Security Considerations

### Passwords & Secrets

```bash
# Use environment variables (never hardcode)
export DB_PASSWORD=<strong_password>

# Or use .env files (add to .gitignore)
echo "DB_PASSWORD=<strong_password>" >> .env

# Production: Use secrets manager
# - AWS Secrets Manager
# - Kubernetes Secrets
# - HashiCorp Vault
```

### HTTPS/SSL

```bash
# Generate self-signed certificate (development)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Production: Use Let's Encrypt
certbot certonly --standalone -d triangulation.example.com
```

### Database Security

```bash
# Create dedicated database user
createuser -P triangulation_user

# Grant minimal permissions
psql -U postgres -c "GRANT CONNECT ON DATABASE mycroft_triangulation TO triangulation_user;"
psql -U postgres -d mycroft_triangulation -c "GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO triangulation_user;"
```

---

## Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh - Daily backup script

BACKUP_DIR="/backups/triangulation"
DB_NAME="mycroft_triangulation"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U postgres $DB_NAME | gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Backup configuration
tar -czf $BACKUP_DIR/config_$TIMESTAMP.tar.gz \
  /app/backend/.env \
  /app/frontend/.env

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

### Recovery Procedure

```bash
# Restore database from backup
gunzip -c backups/db_20260617_150000.sql.gz | \
  psql -U postgres mycroft_triangulation

# Verify restoration
psql -U postgres -d mycroft_triangulation -c "SELECT COUNT(*) FROM signals;"
```

---

## Performance Tuning

### Database

```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM signals WHERE company_name = 'OpenAI';

-- Create additional indexes if needed
CREATE INDEX idx_signals_type_confidence ON signals(signal_type, confidence DESC);

-- Vacuum and analyze
VACUUM ANALYZE;
```

### Java Application

```bash
# Tune JVM parameters
export JAVA_OPTS="-Xms1024m -Xmx2048m -XX:+UseG1GC -XX:MaxGCPauseMillis=200"

# Enable profiling
export JAVA_OPTS="$JAVA_OPTS -XX:+UnlockDiagnosticVMOptions -XX:+DebugNonSafepoints"
```

### Frontend

```bash
# Enable compression
nginx: gzip on; gzip_types text/plain application/json;

# Enable caching
expires 1h; # for static assets
```

---

## Summary

The Triangulation Validator is ready for:

✅ **Local Development** - Docker Compose for rapid iteration  
✅ **Testing** - Integrated test suite with Jest/JUnit  
✅ **Staging** - Multi-container orchestration  
✅ **Production** - Kubernetes-ready with monitoring  
✅ **Scaling** - Horizontal scaling via load balancer  

**Next Steps:**
1. Set up CI/CD pipeline (GitHub Actions, GitLab CI, Jenkins)
2. Configure monitoring (Prometheus, Grafana, ELK)
3. Implement alerting (PagerDuty, Opsgenie)
4. Plan disaster recovery
5. Establish runbooks for common issues

