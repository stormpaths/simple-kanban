---
description: Standard project templates and patterns
---

# Project Templates

## Container Registry Standards

All container images should be built and tagged consistently:
- Use `registry.stormpath.net/[project-name]` as image repository
- Use semantic versioning for production releases
- Include git commit hash for development builds
- Follow naming convention: `registry.stormpath.net/[project-name]:[version]`

## Container-First Development Standards

All projects must follow these containerization principles:

### Security Requirements
- **Non-root user**: All containers run with dedicated user (uid:gid 1000:1000)
- **Minimal base images**: Use official slim/alpine variants
- **Multi-stage builds**: Separate build and runtime environments
- **Security scanning**: Integrate vulnerability scanning in CI/CD

### File Structure Standards
```
project-name/
├── src/                    # Source code
├── tests/                  # Test files
├── docs/                   # Documentation
├── helm/                   # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
├── Dockerfile              # Multi-stage container build
├── Makefile               # Standard targets: test, lint, deploy
├── skaffold.yaml          # Development workflow
├── requirements.txt       # Dependencies (Python)
├── .gitignore
├── .dockerignore
└── README.md
```

### Required Makefile Targets

All projects must include these standardized Makefile targets:

```makefile
setup:          # Setup development environment
test:           # Run all tests (unit + integration)
lint:           # Run comprehensive linting and security checks
build:          # Build application/container
run:            # Run application locally
deploy:         # Deploy to dev environment (default)
deploy-dev:     # Deploy to development
deploy-prod:    # Deploy to production
clean:          # Clean build artifacts
security:       # Run security scans

# Python-specific linting targets
lint-python:    # Black, Ruff, Pyright
lint-security:  # Checkov, Bandit, Safety
lint-check:     # Check formatting without changes
lint-format:    # Auto-format code
fix-black:      # Auto-fix with Black
fix-ruff:       # Auto-fix with Ruff
```

### Helm Chart Requirements
- **Resource limits**: Always define CPU/memory limits
- **Health checks**: Liveness and readiness probes
- **Security context**: Non-root, read-only filesystem where possible
- **ConfigMaps/Secrets**: Externalize configuration
- **Horizontal Pod Autoscaler**: For production workloads

### Skaffold Configuration Standards

#### Database and Cache Integration
Applications requiring PostgreSQL and Redis should deploy Redis as part of the application stack and use CloudNativePG (CNPG) for PostgreSQL.

```yaml
deploy:
  helm:
    releases:
    # PostgreSQL managed by CNPG - see infra/kubernetes/cnpg/clusters/
    - name: app-redis
      chartPath: ../../infra/kubernetes/charts/redis-cache
      setValues:
        auth.enabled: true
        auth.existingSecret: app-redis-secret
        auth.existingSecretPasswordKey: redis-password
        persistence.enabled: false
```

#### Environment-Specific Configuration
- **Development**: Simple passwords, smaller storage (8Gi), metrics disabled
- **Production**: Environment variable passwords, larger storage (100Gi/20Gi), metrics enabled

#### Port Forwarding Standards
```yaml
portForward:
- resourceType: service
  resourceName: app-name
  port: 8000
  localPort: 8000
- resourceType: service
  resourceName: app-postgres
  port: 5432
  localPort: 5432
- resourceType: service
  resourceName: app-redis-master
  port: 6379
  localPort: 6379
```

#### Service Naming Convention
- PostgreSQL: `{app-name}-postgres`
- Redis: `{app-name}-redis-master`
- Application: `{app-name}`

### Testing Standards
- **Unit tests**: Minimum 80% coverage
- **Integration tests**: API endpoint testing
- **Security tests**: Container scanning, dependency checks
- **Performance tests**: Load testing for APIs

## Language-Specific Templates

### Python Template
- **Framework**: FastAPI for APIs, Flask for simple web apps
- **Testing**: pytest with coverage reporting
- **Linting**: black, flake8, mypy
- **Dependencies**: requirements.txt with pinned versions
- **ASGI Server**: uvicorn with gunicorn workers

### Go Template
- **Framework**: Gin or Echo for web services
- **Testing**: Go standard testing with testify
- **Linting**: golangci-lint
- **Dependencies**: Go modules with vendor directory
- **Build**: Multi-stage Docker builds

### JavaScript/Node.js Template
- **Framework**: Express.js or Fastify
- **Testing**: Jest with supertest for API testing
- **Linting**: ESLint with Prettier
- **Dependencies**: package-lock.json for reproducible builds
- **Runtime**: Node.js LTS in Alpine container
