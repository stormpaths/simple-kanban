---
description: Process for managing and updating Helm chart versions
---

# Chart Version Management Process

## Overview

Standard process for checking, updating, and maintaining current Helm chart versions in Skaffold configurations.

## Pre-Development Checklist

Before starting any new project or major update, verify chart versions:

### 1. Update Helm Repositories
```bash
helm repo update
```

### 2. Check Latest Chart Versions
```bash
# Redis image tags
docker pull redis:alpine

# Other common charts
helm search repo bitnami/mysql --versions | head -5
helm search repo bitnami/mongodb --versions | head -5
helm search repo bitnami/elasticsearch --versions | head -5
```

### 3. Update Skaffold Configuration
Update `skaffold.yaml` with latest stable versions:

```yaml
# Current latest versions (as of 2025-08-27)
- name: app-redis
  chartPath: ../../infra/kubernetes/charts/redis-cache
  setValues:
    auth.enabled: true
    auth.existingSecret: app-redis-secret
    auth.existingSecretPasswordKey: redis-password
    persistence.enabled: false
```

PostgreSQL is managed by CloudNativePG (CNPG) and is not tracked as a Helm chart version.

## Version Selection Criteria

### Stability Priority
1. **Latest stable release** (preferred for new projects)
2. **Previous stable release** (for conservative environments)
3. **Avoid pre-release versions** (alpha, beta, rc)

### Compatibility Checks
- Verify application compatibility with new database versions
- Check breaking changes in chart release notes
- Test in development environment before production

## Documentation Requirements

### Update Standards Documentation
When chart versions change, update:
- `skaffold-database-patterns.md`
- `project-templates.md`
- Any project-specific documentation

### Version History Tracking
Maintain a changelog of version updates:

```markdown
## Chart Version History

### 2025-08-27
- PostgreSQL: 13.2.24 → 16.7.11 (PostgreSQL 15.x → 17.5.0)
- Redis: 18.19.4 → 21.2.3 (Redis 7.x → 8.0.2)
- Reason: Security updates and performance improvements
```

## Automation Recommendations

### Makefile Target
Add to project Makefile:
```makefile
check-chart-versions:
	@echo "Checking latest chart versions..."
	@helm repo update
	@echo "Redis: check image tags manually"

update-chart-versions:
	@echo "Update skaffold.yaml with latest versions manually"
	@echo "Then run: make check-chart-versions"
```

### CI/CD Integration
Consider adding automated checks:
```yaml
# .github/workflows/chart-version-check.yml
name: Chart Version Check
on:
  schedule:
    - cron: '0 9 * * MON'  # Weekly Monday check
  workflow_dispatch:

jobs:
  check-versions:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: azure/setup-helm@v3
    - name: Check Chart Versions
      run: |
        make check-chart-versions
```

## Security Considerations

### Version Pinning
- Always pin exact versions in production
- Use version ranges only in development
- Document security patches and updates

### Vulnerability Scanning
```bash
# Check for known vulnerabilities
docker run --rm aquasec/trivy image redis:alpine
```

## Best Practices

1. **Regular Updates**: Check monthly for security updates
2. **Testing**: Always test version updates in development first
3. **Documentation**: Update all references when versions change
4. **Rollback Plan**: Maintain ability to rollback to previous versions
5. **Communication**: Notify team of breaking changes

## Common Charts and Current Versions

| Chart | Current Version | App Version | Last Updated |
|-------|----------------|-------------|--------------|
| bitnami/mysql | 11.1.15 | 8.4.2 | 2025-08-27 |
| bitnami/mongodb | 16.0.1 | 8.0.1 | 2025-08-27 |

## Troubleshooting

### Version Compatibility Issues
1. Check chart release notes for breaking changes
2. Review application compatibility matrix
3. Test with previous stable version if needed
4. Consult upstream chart documentation

### Update Failures
1. Verify Helm repository is updated
2. Check network connectivity
3. Validate YAML syntax
4. Review Kubernetes cluster compatibility
