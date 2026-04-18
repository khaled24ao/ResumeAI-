# Changelog

All notable changes to ResumeAI project will be documented in this file.

## [1.1.0] - 2025-04-18 - Production Ready Edition

### Added
- **Database Persistence**: SQLAlchemy ORM with PostgreSQL/SQLite support
  - Analysis history storage with full CRUD
  - Statistics aggregation (avg score, top keywords)
  - Pagination and sorting
  
- **Rate Limiting**: Flask-Limiter with Redis backend
  - Global limits: 100/day, 20/hour (configurable)
  - Per-endpoint customizable limits
  - Rate limit status endpoint

- **Multi-language Support (i18n)**:
  - English and Arabic translations
  - Frontend language selector with RTL support
  - Extensible translation system

- **Monitoring & Observability**:
  - Prometheus metrics endpoint (`/metrics`)
  - Custom metrics: HTTP requests, latency, Groq API calls, PDF processing time
  - Grafana dashboard for visualization
  - Structured JSON logging

- **CI/CD Pipeline**:
  - GitHub Actions workflow
  - Automated testing with pytest
  - Linting with ruff & mypy
  - Security scanning (bandit, trivy)
  - Docker image builds on push

- **Comprehensive Testing**:
  - Unit tests: services, models, schemas, utils
  - Integration tests: full API workflow
  - Coverage reporting (80%+ target)
  - Test fixtures and mocks

- **Production Infrastructure**:
  - Multi-service Docker Compose (Postgres, Redis, Prometheus, Grafana)
  - Gunicorn WSGI server
  - Non-root container user
  - Health & readiness probes

- **Developer Experience**:
  - Pre-commit hooks (ruff, black, mypy, bandit)
  - Type hints throughout codebase
  - Comprehensive docstrings
  - Error handling & retry logic (tenacity)
  - Pydantic validation for all inputs/outputs

### Changed
- Upgrade to Python 3.13
- Flask 3.x compatibility
- Improved AI prompt engineering
- Structured error responses
- Better PDF error handling

### Security
- File type validation
- File size limits enforced
- Encrypted PDF detection
- SQL injection prevention (SQLAlchemy)
- XSS protection (input sanitization)

## [1.0.0] - 2025-04-10 - Initial Release

### Added
- Basic CV analysis with Groq LLaMA
- PDF text extraction (pypdf)
- Simple Flask web interface
- Docker containerization
- Basic error handling