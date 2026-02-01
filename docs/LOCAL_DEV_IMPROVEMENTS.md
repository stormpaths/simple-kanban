# 🔧 Local Development Improvements Plan
**Date:** October 13, 2025  
**Status:** Proposed Changes

---

## 🎯 Objectives

1. **Remove docker-compose references** - All development via Skaffold
2. **Add local profile** - Sane defaults for localhost development
3. **Optional ingress** - Disable ingress for local, use port-forward instead

---

## 📋 Changes Required

### 1. Remove docker-compose References

**Files to Update:**
- ✅ `README.md` - Remove docker-compose monitoring commands
- ✅ `docs/local-monitoring-stack.md` - Update to Skaffold-based approach
- ✅ `docs/04-architecture-options.md` - Historical, mark as outdated
- ✅ `docs/06-requirements-review.md` - Historical, mark as outdated
- ✅ `docs/07-project-rules.md` - Update to reflect Skaffold-first
- ✅ `docs/09-development-stories.md` - Historical, mark as completed differently
- ✅ `docs/observability-architecture.md` - Update monitoring setup
- ✅ Various evaluation/summary docs - Leave as historical records

**Keep docker-compose for:**
- ❌ `tests/frontend/docker-compose.yml` - Required for Playwright tests
- ❌ `docker-compose.monitoring.yml` - Optional monitoring stack

---

### 2. Add Skaffold Local Profile

**New File:** `helm/simple-kanban/values-local.yaml`

```yaml
# Local development values
replicaCount: 1

image:
  repository: simple-kanban
  tag: latest
  pullPolicy: IfNotPresent

env:
  OTEL_SERVICE_NAME: "simple-kanban-local"
  LOG_LEVEL: "DEBUG"
  SQLALCHEMY_ECHO: "True"

service:
  type: ClusterIP
  port: 80
  targetPort: 8000

# Disable ingress for local - use port-forward instead
ingress:
  enabled: false

# Lighter resource limits for local
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 50m
    memory: 64Mi

# Faster health checks for local
livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 10
  periodSeconds: 5

readinessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 3
  periodSeconds: 3
```

**Update:** `skaffold.yaml`

```yaml
profiles:
- name: local
  activation:
    - command: dev
  deploy:
    helm:
      releases:
      - name: simple-kanban-local
        chartPath: helm/simple-kanban
        namespace: default
        valuesFiles:
        - helm/simple-kanban/values-local.yaml
  portForward:
  - resourceType: service
    resourceName: simple-kanban-local
    port: 80
    localPort: 8000
```

---

### 3. Update Documentation

**README.md Changes:**

```markdown
## Quick Start

### Local Development (Recommended)
```bash
# Start local development with Skaffold
skaffold dev -p local

# Access application
# http://localhost:8000 (via port-forward)
```

### Development Environment
```bash
# Deploy to dev cluster
skaffold run -p dev

# Access via ingress
# https://kanban.stormpath.dev
```

### Production Deployment
```bash
# Deploy to production
skaffold run -p prod

# Access via ingress
# https://kanban.stormpath.net
```

## Monitoring (Optional)

For local monitoring stack:
```bash
# Start monitoring with Skaffold
skaffold dev -p local-monitoring

# Or use docker-compose for standalone monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```
```

---

### 4. Makefile Updates

**Update `make dev` target:**

```makefile
# Development with Skaffold (local profile)
dev:
	@echo "🚀 Starting local development with Skaffold..."
	@echo ""
	@echo "📍 Application will be available at:"
	@echo "   http://localhost:8000"
	@echo ""
	@echo "⚡ Features:"
	@echo "   - Auto-rebuild on code changes"
	@echo "   - Port-forward to localhost:8000"
	@echo "   - No ingress required"
	@echo ""
	skaffold dev -p local

# Development on cluster (dev profile)
dev-cluster:
	@echo "🚀 Deploying to dev cluster with Skaffold..."
	@echo ""
	@echo "📍 Application will be available at:"
	@echo "   https://kanban.stormpath.dev"
	@echo ""
	skaffold run -p dev

# Remove old docker-compose monitoring target
monitoring-up:
	@echo "📊 Starting monitoring stack..."
	@echo ""
	@echo "⚠️  Note: Monitoring via docker-compose is optional"
	@echo "   For integrated monitoring, use Skaffold profiles"
	@echo ""
	docker-compose -f docker-compose.monitoring.yml up -d
```

---

## 🔄 Migration Path

### Phase 1: Add Local Profile (Immediate)
1. Create `values-local.yaml`
2. Add `local` profile to `skaffold.yaml`
3. Test local development workflow
4. Update `Makefile` with new targets

### Phase 2: Update Documentation (Same PR)
1. Update `README.md` with Skaffold-first approach
2. Mark historical docs as outdated where appropriate
3. Update `docs/local-monitoring-stack.md`
4. Keep docker-compose references only for:
   - Frontend tests (required)
   - Optional monitoring stack

### Phase 3: Deprecation Notices (Future)
1. Add deprecation notice to `docker-compose.yml`
2. Consider removing in v3.0

---

## 📝 Implementation Checklist

### Files to Create
- [ ] `helm/simple-kanban/values-local.yaml`

### Files to Update
- [ ] `skaffold.yaml` - Add local profile
- [ ] `Makefile` - Update dev targets
- [ ] `README.md` - Skaffold-first documentation
- [ ] `docs/local-monitoring-stack.md` - Update approach

### Files to Mark as Historical
- [ ] `docs/04-architecture-options.md` - Add note
- [ ] `docs/06-requirements-review.md` - Add note
- [ ] `docs/09-development-stories.md` - Add note

### Files to Keep As-Is
- ✅ `tests/frontend/docker-compose.yml` - Required for tests
- ✅ `docker-compose.monitoring.yml` - Optional monitoring
- ✅ All evaluation/summary docs - Historical records

---

## 🎯 Benefits

### Developer Experience
- ✅ Single command: `skaffold dev -p local`
- ✅ Auto-reload on code changes
- ✅ No manual port management
- ✅ Consistent with cluster deployments

### Simplified Setup
- ✅ No docker-compose confusion
- ✅ Clear local vs. cluster distinction
- ✅ Port-forward instead of ingress for local
- ✅ Lighter resource requirements

### Consistency
- ✅ Same tool (Skaffold) for all environments
- ✅ Helm charts for all deployments
- ✅ Predictable behavior across environments

---

## 🚀 Recommended Commands After Implementation

```bash
# Local development (new default)
make dev                    # Skaffold dev with local profile
# → http://localhost:8000

# Cluster development
make dev-cluster            # Deploy to dev cluster
# → https://kanban.stormpath.dev

# Production deployment
make deploy                 # Deploy to production
# → https://kanban.stormpath.net

# Testing (unchanged)
make test                   # All tests
make test-frontend          # Frontend tests (still uses docker-compose)

# Monitoring (optional)
make monitoring-up          # Optional docker-compose monitoring
```

---

## ⚠️ Breaking Changes

**None** - This is additive:
- Adds `local` profile (new)
- Keeps existing `dev` and `prod` profiles
- docker-compose still available for monitoring
- Frontend tests unchanged

---

## 📊 Summary

**Goal:** Skaffold-first development with sane local defaults

**Changes:**
1. Add `local` profile with port-forward (no ingress)
2. Update docs to recommend Skaffold
3. Keep docker-compose only where needed (tests, monitoring)
4. Improve developer experience

**Timeline:** 1-2 hours implementation + testing

**Ready to implement?**
