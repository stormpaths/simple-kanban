# Architecture Options Analysis

> **Note:** This is a historical planning document from the initial project phase.
> The project now uses Skaffold + Kubernetes + Helm for all deployments.
> See README.md for current deployment approach.

# Architecture Design Options - Simple Kanban Board

Based on your stormpath app's Redis/PostgreSQL pattern and data persistence requirements, here are three architecture options:

## Option 1: Simple SQLite (Minimal)

### Architecture
- **Backend**: FastAPI with SQLite database
- **Frontend**: Vanilla JavaScript or lightweight framework
- **Deployment**: Single container
- **Data**: File-based SQLite with volume mount

### Components
```
┌─────────────────┐
│   Frontend      │
│  (JavaScript)   │
└─────────────────┘
         │
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└─────────────────┘
         │
┌─────────────────┐
│   SQLite DB     │
│  (Volume Mount) │
└─────────────────┘
```

### Data Persistence Strategy
- SQLite file stored in mounted volume (`/data/kanban.db`)
- Automatic backups via cron job to external storage
- Simple file-based replication for redundancy

### Pros
- **Simplest deployment**: Single container, no external dependencies
- **Fast development**: No database setup complexity
- **Low resource usage**: Minimal memory and CPU requirements
- **Easy backup**: Simple file copy operations
- **Perfect for single-user**: No concurrency issues

### Cons
- **Limited scalability**: Single-user or very small teams only
- **No real-time updates**: Polling required for multi-user scenarios
- **Single point of failure**: If container fails, service is down
- **Limited querying**: SQLite has fewer advanced features

---

## Option 2: Redis + PostgreSQL (Stormpath Pattern)

### Architecture
- **Backend**: FastAPI with PostgreSQL + Redis
- **Frontend**: React/Vue with real-time updates
- **Deployment**: Multi-container with docker-compose
- **Data**: PostgreSQL with Redis caching and sessions

### Components
```
┌─────────────────┐
│   Frontend      │
│ (React/Vue +    │
│  WebSockets)    │
└─────────────────┘
         │
┌─────────────────┐
│   FastAPI       │
│   Backend       │
│ (WebSockets)    │
└─────────────────┘
    │         │
┌─────────┐ ┌─────────┐
│ Redis   │ │PostgreSQL│
│(Cache + │ │(Primary  │
│Sessions)│ │ Data)    │
└─────────┘ └─────────┘
```

### Data Persistence Strategy
- **PostgreSQL**: Primary data storage with volume mounts
- **Redis**: Session storage, real-time updates, task caching
- **Backup**: PostgreSQL dumps + Redis persistence
- **High Availability**: PostgreSQL replication, Redis clustering

### Pros
- **Real-time updates**: WebSocket support for live collaboration
- **Scalable**: Handles multiple users efficiently
- **Robust caching**: Fast task retrieval and updates
- **Session management**: User authentication and state
- **Production ready**: Battle-tested pattern from stormpath
- **Advanced features**: Complex queries, transactions, ACID compliance

### Cons
- **Complex deployment**: Multiple containers and dependencies
- **Higher resource usage**: More memory and CPU required
- **Maintenance overhead**: Two databases to manage and backup
- **Development complexity**: More moving parts to debug

---

## Option 3: Hybrid SQLite + Redis (Balanced)

### Architecture
- **Backend**: FastAPI with SQLite + Redis
- **Frontend**: Modern JavaScript with optional real-time features
- **Deployment**: Two-container setup
- **Data**: SQLite for persistence, Redis for real-time and caching

### Components
```
┌─────────────────┐
│   Frontend      │
│ (JavaScript +   │
│ Optional WS)    │
└─────────────────┘
         │
┌─────────────────┐
│   FastAPI       │
│   Backend       │
│ (Optional WS)   │
└─────────────────┘
    │         │
┌─────────┐ ┌─────────┐
│ Redis   │ │ SQLite  │
│(Cache + │ │(Primary │
│Real-time│ │ Data)   │
└─────────┘ └─────────┘
```

### Data Persistence Strategy
- **SQLite**: Primary data with volume mount
- **Redis**: Real-time updates, task state caching
- **Backup**: SQLite file backup + Redis snapshots
- **Failover**: Redis optional, SQLite as source of truth

### Pros
- **Balanced complexity**: More features than Option 1, simpler than Option 2
- **Optional real-time**: Can add WebSockets later if needed
- **Good performance**: Redis caching with SQLite reliability
- **Easier migration**: Can upgrade to PostgreSQL later
- **Cost effective**: Lower resource requirements than full PostgreSQL

### Cons
- **SQLite limitations**: Still limited by SQLite's concurrency model
- **Partial redundancy**: Redis and SQLite serve different purposes
- **Medium complexity**: More complex than single container

---

## Recommendation for Your Use Case

Given your requirements for **data persistence during node failures** and **ownership/control**, I recommend:

### **Start with Option 3 (Hybrid)** for these reasons:

1. **Data Safety**: SQLite file in mounted volume survives container restarts
2. **Growth Path**: Can add real-time features and scale up later
3. **Familiar Pattern**: Similar to stormpath but simpler
4. **Node Failure Protection**: Volume mounts persist data across node failures
5. **Easy Backup**: Simple file-based backups for SQLite

### **Volume Mount Strategy for Node Failure Protection**:
```yaml
# In Helm chart
volumes:
  - name: kanban-data
    persistentVolumeClaim:
      claimName: kanban-data-pvc
      
# PVC with storage class that replicates across nodes
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: kanban-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: "replicated-storage"  # Your cluster's replicated storage
  resources:
    requests:
      storage: 1Gi
```

Would you like me to proceed with **Option 3 (Hybrid)** and design the detailed system architecture and data models?
