# Multi-stage build for Triangulation Validator

# Stage 1: Backend build
FROM maven:3.9.16-eclipse-temurin-21 AS backend-builder
WORKDIR /app/backend
COPY backend/pom.xml .
COPY backend/src ./src
RUN mvn clean package -DskipTests

# Stage 2: Frontend build
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/src ./src
COPY frontend/index.html ./
COPY frontend/vite.config.ts ./
COPY frontend/tsconfig.json ./
COPY frontend/tailwind.config.js ./
RUN npm run build

# Stage 3: Runtime
FROM eclipse-temurin:21-jdk-slim
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy backend JAR
COPY --from=backend-builder /app/backend/target/triangulation-validator-0.1.0.jar ./app.jar

# Copy frontend to serve statically
COPY --from=frontend-builder /app/frontend/dist ./static

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/v1/health || exit 1

# Expose ports
EXPOSE 8080

# Environment defaults
ENV JAVA_OPTS="-Xmx512m -Xms256m"
ENV DATABASE_URL="jdbc:postgresql://db:5432/mycroft_triangulation"
ENV DB_USER="postgres"
ENV DB_PASSWORD="postgres"

# Run application
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
