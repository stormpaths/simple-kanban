---
description: Skaffold database and cache deployment patterns
---

# Skaffold Database and Cache Patterns

## Overview

Standard patterns for deploying PostgreSQL and Redis alongside applications using Skaffold.

## PostgreSQL Integration

### Basic Configuration
```yaml
# PostgreSQL is managed by CloudNativePG (CNPG) via manifests
# See: infra/kubernetes/cnpg/clusters/
```

### Environment-Specific Values

#### Development
```yaml
# Use the CNPG cluster in your target namespace
# - {cluster-name}-rw service for writes
# - {cluster-name}-ro service for reads
```

#### Production
```yaml
# Use the CNPG cluster in your target namespace
# - {cluster-name}-rw service for writes
# - credentials stored in a CNPG-format secret (username/password keys)
```

## Redis Integration

### Basic Configuration
```yaml
- name: app-redis
  chartPath: ../../infra/kubernetes/charts/redis-cache
  setValues:
    auth.enabled: true
    auth.existingSecret: app-redis-secret
    auth.existingSecretPasswordKey: redis-password
    persistence.enabled: false
```

### Environment-Specific Values

#### Development
```yaml
setValues:
  auth.password: simple-dev-password
  master.persistence.size: 8Gi
  metrics.enabled: false
```

#### Production
```yaml
setValues:
  auth.password: ${REDIS_PASSWORD}
  master.persistence.size: 20Gi
  metrics.enabled: true
  master.resources:
    limits:
      cpu: 1000m
      memory: 2Gi
    requests:
      cpu: 500m
      memory: 1Gi
```

## Complete Skaffold Example

```yaml
apiVersion: skaffold/v4beta7
kind: Config
metadata:
  name: example-app
build:
  artifacts:
  - image: example-app
    docker:
      dockerfile: Dockerfile
  local:
    push: false
deploy:
  helm:
    releases:
    - name: example-app-redis
      chartPath: ../../infra/kubernetes/charts/redis-cache
      setValues:
        auth.enabled: true
        auth.existingSecret: example-app-redis-secret
        auth.existingSecretPasswordKey: redis-password
        persistence.enabled: false
    - name: example-app
      chartPath: helm/example-app
      valuesFiles:
      - helm/example-app/values-dev.yaml
      setValues:
        image.repository: example-app
        image.tag: example-app
portForward:
- resourceType: service
  resourceName: example-app
  port: 8000
  localPort: 8000
- resourceType: service
  resourceName: example-app-redis-master
  port: 6379
  localPort: 6379
profiles:
- name: dev
  deploy:
    helm:
      releases:
      - name: example-app-redis
        chartPath: ../../infra/kubernetes/charts/redis-cache
        setValues:
          auth.enabled: true
          auth.existingSecret: example-app-redis-secret
          auth.existingSecretPasswordKey: redis-password
          persistence.enabled: false
      - name: example-app
        chartPath: helm/example-app
        valuesFiles:
        - helm/example-app/values-dev.yaml
- name: prod
  deploy:
    helm:
      releases:
      - name: example-app-redis
        chartPath: ../../infra/kubernetes/charts/redis-cache
        setValues:
          auth.enabled: true
          auth.existingSecret: example-app-redis-secret
          auth.existingSecretPasswordKey: redis-password
          persistence.enabled: false
      - name: example-app
        chartPath: helm/example-app
        valuesFiles:
        - helm/example-app/values-prod.yaml
```

## Application Configuration

### Helm Values Integration

#### Development Values (values-dev.yaml)
```yaml
storage:
  postgres:
    hostname: example-app-postgres
    username: appuser
    database: appdb
    password: dev-password

cache:
  redis:
    hostname: example-app-redis-master
    password: dev-password
```

#### Production Values (values-prod.yaml)
```yaml
storage:
  postgres:
    hostname: example-app-postgres-rw
    username: appuser
    database: appdb
    credentialsSecret: example-app-cnpg-secret
    userPasswordKey: password

cache:
  redis:
    hostname: example-app-redis-master
    credentialsSecret: example-app-redis-secret
    passwordKey: redis-password
```

## Service Naming Conventions

- **PostgreSQL Service**: `{app-name}-postgres`
- **Redis Master Service**: `{app-name}-redis-master`
- **Redis Replica Service**: `{app-name}-redis-replica` (if replicas enabled)

## Best Practices

1. **Version Pinning**: Always specify exact chart versions
2. **Resource Limits**: Define appropriate CPU/memory limits for production
3. **Persistence**: Use appropriate storage sizes for each environment
4. **Metrics**: Enable metrics collection in production environments
5. **Security**: Use Kubernetes secrets for production passwords
6. **Port Forwarding**: Include database ports for local development access

## Environment Variables for Production

```bash
# PostgreSQL
export POSTGRES_PASSWORD="secure-postgres-password"
export DB_USER="appuser"
export DB_PASSWORD="secure-user-password"
export DB_NAME="appdb"

# Redis
export REDIS_PASSWORD="secure-redis-password"

# Storage
export PG_STORAGE="100Gi"
export REDIS_STORAGE="20Gi"

# Monitoring
export ENABLE_METRICS="true"
```
