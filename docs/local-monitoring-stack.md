# Local Monitoring Stack - Simple Kanban Board

## Overview

A complete Prometheus and Grafana monitoring stack for local development and lower environments. This stack can be easily configured to forward metrics to centralized production clusters while providing immediate observability during development.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Simple Kanban  │───▶│   Prometheus    │───▶│    Grafana      │
│     :8000       │    │     :9090       │    │     :3000       │
│   /metrics      │    │                 │    │   Dashboards    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  AlertManager   │
                       │     :9093       │
                       │    Alerts       │
                       └─────────────────┘
```

## Quick Start

### 1. Start the Application
```bash
# Start local development with Skaffold
make dev

# Application will be available at http://localhost:8000
```

### 2. Start the Monitoring Stack (Optional)
```bash
# Start standalone monitoring stack
make monitoring-up

# Or use docker-compose directly
docker-compose -f docker-compose.monitoring.yml up -d
```

### 3. Access Services
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093
- **Application Metrics**: http://localhost:8000/metrics

### 3. View Dashboards
- Navigate to Grafana → Dashboards → "Simple Kanban Board - Overview"
- Pre-configured panels for HTTP metrics, business metrics, and system health

## Configuration Files

### Prometheus Configuration
- **Location**: `monitoring/prometheus/prometheus.yml`
- **Scrape Targets**: Application metrics, system metrics, database metrics
- **Retention**: 15 days of metrics data
- **Remote Write**: Commented configuration for production forwarding

### Grafana Dashboards
- **Auto-provisioned**: Dashboards load automatically on startup
- **Location**: `monitoring/grafana/dashboards/`
- **Includes**: Application overview, business metrics, system health

### Alert Rules
- **Location**: `monitoring/prometheus/rules/simple-kanban.yml`
- **Alerts**: High error rate, latency, service down, database issues
- **Thresholds**: Configurable for development vs production

## Metrics Collected

### Application Metrics
```prometheus
# HTTP Request metrics
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint}

# Business metrics
kanban_tasks_created_total{project_id}
kanban_tasks_completed_total{project_id}
kanban_active_users

# Database metrics
db_connections_active
db_query_duration_seconds{operation}

# Redis metrics
redis_operations_total{operation}
redis_cache_hit_rate
```

### System Metrics (Optional)
- **Node Exporter**: CPU, memory, disk, network
- **PostgreSQL Exporter**: Database performance
- **Redis Exporter**: Cache performance

## Production Forwarding

### Remote Write Configuration
Enable remote write in `monitoring/prometheus/prometheus.yml`:

```yaml
remote_write:
  - url: "https://prometheus-gateway.production.example.com/api/v1/write"
    basic_auth:
      username: "kanban-app"
      password_file: "/etc/prometheus/remote-write-password"
    queue_config:
      max_samples_per_send: 1000
      max_shards: 200
      capacity: 2500
```

### Grafana Federation
Configure Grafana to query both local and production Prometheus:

```yaml
# Additional datasource for production
- name: Production Prometheus
  type: prometheus
  url: https://prometheus.production.example.com
  access: proxy
  basicAuth: true
  basicAuthUser: grafana-reader
```

## Resource Requirements

### Development Environment
- **CPU**: ~200m (0.2 cores) total for monitoring stack
- **Memory**: ~512MB total (Prometheus: 256MB, Grafana: 128MB, AlertManager: 64MB)
- **Storage**: ~1GB for 15 days of metrics retention
- **Network**: Minimal impact, scraping every 15 seconds

### Overhead Assessment
**Monitoring stack adds minimal overhead:**
- ✅ **Lightweight**: Uses official slim images
- ✅ **Configurable**: Retention and scraping intervals adjustable
- ✅ **Optional**: Can be disabled for resource-constrained environments
- ✅ **Isolated**: Runs in separate Docker network

## Dashboard Features

### Application Overview Dashboard
- **HTTP Metrics**: Request rate, response time percentiles, error rate
- **Business Metrics**: Task creation/completion rates, active users
- **System Health**: Service availability, database connections
- **Alerts**: Visual indicators for active alerts

### Custom Panels
- **SLA Tracking**: 99.9% availability target visualization
- **Performance Trends**: Week-over-week comparison
- **Capacity Planning**: Resource usage trends
- **User Activity**: Peak usage patterns

## Alert Configuration

### Development Alerts
```yaml
# Relaxed thresholds for development
- alert: HighErrorRate
  expr: error_rate > 10%  # Higher threshold
  for: 10m               # Longer duration

- alert: HighLatency
  expr: p95_latency > 1s  # More lenient
  for: 10m
```

### Production Alerts
```yaml
# Strict thresholds for production
- alert: HighErrorRate
  expr: error_rate > 1%   # Lower threshold
  for: 2m                # Faster response

- alert: HighLatency
  expr: p95_latency > 200ms
  for: 2m
```

## Troubleshooting

### Common Issues

**Prometheus not scraping application:**
```bash
# Check if application metrics endpoint is accessible
curl http://localhost:8000/metrics

# Check Prometheus targets
# Navigate to http://localhost:9090/targets
```

**Grafana dashboard not loading:**
```bash
# Check if datasource is configured
docker-compose logs grafana

# Verify Prometheus connectivity from Grafana
# Navigate to Grafana → Configuration → Data Sources
```

**High resource usage:**
```bash
# Reduce scraping frequency
# Edit monitoring/prometheus/prometheus.yml
scrape_interval: 30s  # Instead of 15s

# Reduce retention period
--storage.tsdb.retention.time=7d  # Instead of 15d
```

## Development Workflow

### 1. Local Development
```bash
# Start with monitoring
make dev-with-monitoring

# View metrics during development
curl http://localhost:8000/metrics | grep kanban_

# Check Grafana dashboards
open http://localhost:3000
```

### 2. Testing Alerts
```bash
# Simulate high error rate
# Send requests that return 500 errors

# Simulate high latency
# Add artificial delays to endpoints

# Check AlertManager
open http://localhost:9093
```

### 3. Dashboard Development
```bash
# Edit dashboards in Grafana UI
# Export JSON and save to monitoring/grafana/dashboards/

# Or edit JSON directly and restart Grafana
docker-compose restart grafana
```

## Integration with CI/CD

### Automated Testing
```yaml
# .github/workflows/test.yml
- name: Start monitoring stack
  run: docker-compose -f docker-compose.monitoring.yml up -d

- name: Wait for Prometheus
  run: |
    timeout 60 bash -c 'until curl -f http://localhost:9090/-/ready; do sleep 2; done'

- name: Test metrics endpoint
  run: |
    curl -f http://localhost:8000/metrics
    
- name: Validate dashboard
  run: |
    # Check if Grafana can query Prometheus
    curl -f "http://admin:admin123@localhost:3000/api/datasources/proxy/1/api/v1/query?query=up"
```

### Production Deployment
```yaml
# Helm values for production
monitoring:
  local:
    enabled: false  # Disable local stack
  remoteWrite:
    enabled: true
    endpoint: "https://prometheus-gateway.prod.example.com/api/v1/write"
    credentials:
      secretName: "prometheus-remote-write"
```

This monitoring stack provides comprehensive observability for development while maintaining a clear path to production integration. The overhead is minimal and the benefits for debugging and performance optimization are substantial.
