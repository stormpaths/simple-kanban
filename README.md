# Simple Kanban Board

A self-hosted kanban board application with drag-and-drop functionality, authentication, group collaboration, and comprehensive testing - built for complete ownership and customization.

## 🎉 Status: PRODUCTION READY WITH COLLABORATION ✅

**Current Version**: v2.0 (Full-Featured Production System)  
**Last Updated**: October 4, 2025  
**Branch**: `kanban-main1`

### 🚀 **Major Updates (October 4, 2025)**
- ✅ **Complete Authentication System** - JWT + API keys with Google OIDC
- ✅ **Group Collaboration** - Full team-based board sharing and management
- ✅ **Automated Testing** - Comprehensive test battery with Skaffold integration
- ✅ **Security Hardening** - Rate limiting, CSRF protection, security headers
- ✅ **Admin Interface** - Complete administrative dashboard and statistics

## Overview

This project provides a containerized kanban board that you fully own and control, with no vendor lock-in or licensing concerns. Built with FastAPI backend, PostgreSQL database, and modern web frontend.

## ✅ Complete Feature Set (Production Ready)

### 🎯 **Core Kanban Features**
- **Complete Kanban Functionality**: Full CRUD operations for boards, columns, and tasks
- **Drag-and-Drop**: Tasks move between columns with full persistence
- **Task Aging**: Color-coded indicators showing "days open" (blue→green→orange→red)
- **Board Management**: Multiple boards with persistent selection across sessions
- **Modern UI**: Responsive design with animations and professional styling
- **Self-Hosted**: Complete Kubernetes deployment with PostgreSQL backend
- **Data Persistence**: All changes persist correctly across page refreshes and restarts

### 🔐 **Authentication & Authorization**
- **JWT Authentication**: Secure token-based authentication with automatic refresh
- **Google OIDC Integration**: Single sign-on with Google accounts
- **API Key Management**: Programmatic access with scoped permissions
- **Dual Authentication**: Support for both JWT tokens and API keys
- **User Registration**: Complete signup and login workflows

### 👥 **Group Collaboration**
- **Group Management**: Create and manage teams for collaboration
- **Group-Owned Boards**: Boards shared with entire groups automatically
- **Member Management**: Add/remove users from groups with role-based permissions
- **Seamless Access**: Group boards appear alongside personal boards
- **Access Control**: Proper authorization for group resources

### 🛡️ **Security & Hardening**
- **Rate Limiting**: Redis-based rate limiting with memory fallback
- **Security Headers**: CSP, HSTS, XSS protection, frame options
- **CSRF Protection**: Token-based protection for state-changing operations
- **JWT Security**: Enforced secure key generation and validation
- **Input Validation**: Comprehensive request validation and sanitization

### 🧪 **Testing & Quality Assurance**
- **Automated Testing**: Comprehensive test battery with Skaffold integration
- **Post-Deploy Validation**: Automatic testing after every deployment
- **Multi-Environment Testing**: Different test modes for dev/prod environments
- **API Testing**: Complete endpoint validation with authentication
- **Group Testing**: Full collaboration workflow validation

### 🔧 **Admin & Management**
- **Admin Dashboard**: Complete administrative interface
- **User Management**: View and manage system users
- **Statistics**: Real-time system metrics and usage statistics
- **API Key Administration**: Manage system-wide API access
- **Health Monitoring**: Comprehensive health checks and status reporting

## Current Architecture

### Backend Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API Design**: RESTful endpoints with proper HTTP status codes
- **Data Models**: Board → Column → Task hierarchy

### Frontend Stack
- **Technology**: Vanilla JavaScript (ES6+)
- **Styling**: Modern CSS with Flexbox/Grid
- **Icons**: FontAwesome integration
- **State Management**: Class-based architecture with localStorage persistence

### Deployment Stack
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes with Helm charts
- **Development**: Skaffold for rapid iteration
- **Database**: PostgreSQL with automated migrations

## Quick Start

### Development
```bash
# Clone and setup
git clone https://github.com/your-repo/simple-kanban.git
cd simple-kanban

# Start development environment with Skaffold
skaffold dev --port-forward

# Access application
# Application: http://127.0.0.1:4503
# API docs: http://127.0.0.1:4503/docs
```

### Local Monitoring Stack
```bash
# Start Prometheus + Grafana + AlertManager
make monitoring-up

# Access monitoring services
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
# Application metrics: http://localhost:8000/metrics
```

### Production Deployment
```bash
# Build and deploy with Helm
make build
make deploy
```

### Docker Run
```bash
# Simple single-container deployment
docker run -p 8000:8000 -v kanban-data:/app/data simple-kanban:latest
```

## Project Structure

```
simple-kanban/
├── helm/                   # Kubernetes deployment
│   └── simple-kanban/     # Helm chart
├── monitoring/            # Local monitoring stack
│   ├── prometheus/        # Prometheus configuration
│   ├── grafana/          # Grafana dashboards
│   └── alertmanager/     # Alert configuration
├── scripts/               # Utility scripts
│   └── generate-secrets.py # SOPS secret generation
├── docs/                  # Documentation
│   └── *.md              # Project documentation
├── .ai-config/           # AI workflow configuration
├── Dockerfile            # Container definition
├── pyproject.toml        # Python dependencies
└── Makefile             # Development commands tests
### API Endpoints

### Application
- `GET /` - Kanban board web interface
- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation (requires authentication)

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login (JWT)
- `GET /api/auth/profile` - Get user profile
- `POST /api/auth/change-password` - Change password
- `GET /api/auth/google` - Google OIDC login

### Boards
- `GET /api/boards/` - List accessible boards (personal + group)
- `POST /api/boards/` - Create new board (personal or group-owned)
- `GET /api/boards/{id}` - Get board details
- `PUT /api/boards/{id}` - Update board
- `DELETE /api/boards/{id}` - Delete board

### Groups & Collaboration
- `GET /api/groups/` - List user's groups
- `POST /api/groups/` - Create new group
- `GET /api/groups/{id}` - Get group details with members
- `PUT /api/groups/{id}` - Update group information
- `DELETE /api/groups/{id}` - Delete group
- `POST /api/groups/{id}/members` - Add member to group
- `DELETE /api/groups/{id}/members/{user_id}` - Remove member from group

### API Keys
- `GET /api/api-keys/` - List user's API keys
- `POST /api/api-keys/` - Create new API key
- `GET /api/api-keys/{id}` - Get API key details
- `PUT /api/api-keys/{id}` - Update API key
- `DELETE /api/api-keys/{id}` - Delete API key
- `GET /api/api-keys/stats/usage` - API key usage statistics

### Admin
- `GET /api/admin/stats` - System statistics
- `GET /api/admin/users` - List all users (admin only)

### Columns & Tasks
- `GET /api/columns/board/{board_id}` - Get columns with tasks for a board
- `POST /api/tasks/` - Create new task
- `PUT /api/tasks/{id}` - Update task
- `POST /api/tasks/{id}/move` - Move task between columns
- `DELETE /api/tasks/{id}` - Delete task
- `GET /api/tasks/{id}/comments` - Get task comments
- `POST /api/tasks/{id}/comments` - Add task comment

## Configuration

### Environment Variables
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `WORKERS`: Number of worker processes
- `OTEL_SERVICE_NAME`: OpenTelemetry service name
- `OTEL_EXPORTER_OTLP_ENDPOINT`: Prometheus Gateway endpoint
- `OTEL_EXPORTER_OTLP_PROTOCOL`: Protocol (http/protobuf or grpc)

### Helm Values

- **Development**: `helm/values-dev.yaml`
- **Production**: `helm/values-prod.yaml`

## Security

- Non-root container user (uid:gid 1000:1000)
- Read-only root filesystem
- Security contexts in Kubernetes
- Health checks and resource limits
- Vulnerability scanning with Trivy

## Testing

### Automated Testing (Integrated with Skaffold)
```bash
# Deploy with automatic testing
skaffold run -p dev  # Runs comprehensive test battery automatically

# Manual test execution
./scripts/test-all.sh --quick    # Quick smoke tests (~15s)
./scripts/test-all.sh --full     # Full test battery (~45s)
./scripts/test-all.sh --verbose  # Detailed output for debugging
```

### Test Categories
- **Health Checks**: Application availability and responsiveness
- **Comprehensive Authentication**: Complete JWT and API key testing suite
  - User registration and login workflows
  - JWT token validation and protected endpoint access
  - API key authentication and scoped permissions
  - Cross-authentication validation (JWT ↔ API key compatibility)
  - Security controls and invalid authentication rejection
- **API Endpoints**: Complete CRUD operation testing with dual authentication
- **Group Management**: Collaboration workflow validation
- **Admin Functions**: Administrative interface testing with proper access control
- **Security**: Rate limiting, CSRF protection, and comprehensive access control

### Unit Tests
```bash
pytest tests/ -v --cov=src
```

### Integration Tests
```bash
# Authentication Testing Suite
./scripts/test-auth-comprehensive.sh    # Complete authentication validation
./scripts/test-auth-jwt.sh              # JWT authentication workflow
./scripts/test-auth-registration.sh     # User registration testing
./scripts/test-auth-endpoints.sh        # Dual auth endpoint testing

# Feature Testing
./scripts/test-api-key.sh               # API key management tests
./scripts/test-groups.sh                # Group collaboration tests
./scripts/test-admin.sh                 # Admin interface tests

# Deployment Testing
./scripts/post-deploy-test.sh           # Post-deployment validation
```

### Linting
```bash
black --check src/ tests/
flake8 src/ tests/
mypy src/
```

## Monitoring

- Health checks at `/health`
- Basic metrics at `/metrics`
- Kubernetes probes configured
- Resource monitoring via Kubernetes

## Contributing

1. Follow the development guidelines in `.ai-config/standards/`
2. Write tests for new features
3. Ensure code passes linting
4. Update documentation as needed

## License

[Your License Here]
