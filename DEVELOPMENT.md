# ResumeAI Development Guide

## Quick Start for Developers

### Prerequisites
- Python 3.13+
- Docker & Docker Compose (optional but recommended)
- Git

### Setup

```bash
# Clone repository
git clone <your-repo-url>
cd ResumeAI

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and add your GROQ_API_KEY
nano .env  # or any editor

# Initialize database
python scripts/seed_db.py

# Run development server
python app.py
```

Open http://localhost:5000

### With Docker Compose (All-in-One)

```bash
# Start all services (Postgres, Redis, App, Prometheus, Grafana)
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop all services
docker-compose down
```

Access:
- App: http://localhost:5000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin123)

## Project Structure

```
ResumeAI/
├── backend/                  # Flask application
│   ├── app.py              # Application factory
│   ├── config.py           # Configuration classes
│   ├── models/             # SQLAlchemy models
│   ├── routes/             # Blueprints
│   │   ├── analyze.py      # Main analysis endpoint
│   │   └── history.py      # History & stats endpoints
│   ├── services/           # Business logic
│   │   ├── pdf_service.py  # PDF extraction
│   │   ├── ai_service.py   # Groq integration
│   │   └── database.py     # DB session management
│   ├── schemas/            # Pydantic validation
│   │   └── analysis.py     # AnalysisResult schema
│   ├── utils/              # Utilities
│   │   ├── logger.py       # Structured logging
│   │   ├── metrics.py      # Prometheus metrics
│   │   └── i18n.py         # Internationalization
│   └── middleware/         # Custom middleware
│       └── rate_limit.py  # Rate limiting
├── templates/              # Frontend templates
│   └── index.html          # Single page app
├── translations/           # i18n files
│   ├── en.json            # English
│   └── ar.json            # Arabic
├── monitoring/             # Observability configs
│   ├── prometheus/        # Prometheus config
│   └── grafana/           # Grafana dashboards
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Test fixtures
├── scripts/               # Utility scripts
│   ├── seed_db.py         # DB initialization
│   └── init-db.sh         # Shell wrapper
├── docker-compose.yml     # Full stack deployment
├── Dockerfile             # Production image
├── pytest.ini             # Test configuration
├── mypy.ini               # Type checking config
├── pyproject.toml         # Ruff config
└── .pre-commit-config.yaml # Git hooks
```

## Development Workflow

### Running Tests

```bash
# All tests with coverage
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With verbose output
pytest -vv

# Generate HTML coverage report
pytest --cov=backend --cov-report=html
# Open htmlcov/index.html
```

### Code Quality

```bash
# Install pre-commit hooks (recommended)
pre-commit install

# Run manually
ruff check .              # Linting
mypy backend/ --strict    # Type checking
black --check .          # Code formatting
bandit -r backend/       # Security scan
```

### Database Operations

```bash
# Initialize/Reset DB
python scripts/seed_db.py

# Using alembic migrations (future)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Debugging

```bash
# Run in debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py

# Or via .env
FLASK_ENV=development FLASK_DEBUG=1 python app.py
```

### Adding a New Endpoint

1. Create blueprint in `backend/routes/` (or add to existing)
2. Add route handler with proper validation
3. Register blueprint in `backend/app.py`
4. Add Pydantic schema in `backend/schemas/`
5. Write unit tests in `tests/unit/`
6. Write integration tests in `tests/integration/`
7. Update README API section
8. Add metrics tracking if needed
9. Consider i18n if user-facing

Example:

```python
# backend/routes/new_feature.py
from flask import Blueprint, jsonify, request
from pydantic import BaseModel
from backend.utils.logger import get_logger

logger = get_logger(__name__)
new_feature_bp = Blueprint("new_feature", __name__, url_prefix="/api/v1")

class NewFeatureRequest(BaseModel):
    param: str

@new_feature_bp.route("/new-feature", methods=["POST"])
def handle_new_feature():
    data = request.get_json()
    validated = NewFeatureRequest(**data)
    # ... logic
    return jsonify({"result": "ok"})
```

Then in `app.py`:
```python
from backend.routes.new_feature import new_feature_bp
app.register_blueprint(new_feature_bp)
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | **Required** | Groq API key from console.groq.com |
| `FLASK_ENV` | `production` | `development` or `production` |
| `FLASK_DEBUG` | `0` | Enable debug mode (`1` or `0`) |
| `DATABASE_URL` | `sqlite:///resumeai.db` | Database connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for rate limiting |
| `RATE_LIMIT` | `100/day` | Global rate limit |
| `JWT_SECRET_KEY` | - | JWT signing secret (future) |

### Docker Build

```bash
# Development build
docker build -t resumeai:dev -f Dockerfile.dev .

# Production build
docker build -t resumeai:latest .

# Run with env file
docker run --env-file .env -p 5000:5000 resumeai:latest
```

## Troubleshooting

### PDF Extraction Fails
- Ensure PDF is not encrypted
- Check file is not corrupted
- Some PDFs with complex formatting may fail

### Groq API Errors
- Verify `GROQ_API_KEY` is set and valid
- Check API quota at console.groq.com
- Ensure internet connectivity

### Database Connection Issues
- For PostgreSQL: `DATABASE_URL=postgresql://user:pass@host:port/db`
- Check PostgreSQL is running: `docker-compose ps postgres`
- Verify credentials

### Rate Limit Errors (429)
- Wait for rate limit window to reset
- Adjust limits in `backend/app.py` or via env var
- Use API key for higher limits (future)

### Tests Failing
```bash
# Clear cache
pytest --cache-clear

# Create fresh test database
rm -f test.db
pytest
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Commit Convention

We use [Commitizen](https://commitizen-tools.github.io/commitizen/):
```bash
# Interactive commit
cz commit

# Or conventional format
git commit -m "feat: add user authentication"
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Deployment Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Use strong `JWT_SECRET_KEY` (32+ chars)
- [ ] Configure `DATABASE_URL` (PostgreSQL recommended)
- [ ] Configure `REDIS_URL` for production Redis
- [ ] Set up SSL/TLS (nginx/Traefik reverse proxy)
- [ ] Configure log aggregation (ELK/Loki)
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Schedule database backups
- [ ] Configure error tracking (Sentry)
- [ ] Set up CI/CD pipeline (GitHub Actions already configured)
- [ ] Add custom domain DNS
- [ ] Enable rate limiting per environment
- [ ] Review security headers (CSP, HSTS, etc.)

## Performance Optimization

- Use Redis cache for frequent queries
- Enable gzip compression in nginx
- Optimize PDF text extraction (memory mapping for large files)
- Batch process with Celery (future)
- Use CDN for static assets
- Implement connection pooling

## Security Best Practices

- Never commit `.env` or secrets
- Rotate `GROQ_API_KEY` periodically
- Use HTTPS in production
- Validate and sanitize all inputs
- Implement proper CORS
- Add request signing (HMAC)
- Log security events
- Regular dependency updates (`pip-audit`)

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Groq Docs](https://console.groq.com/docs)
- [pypdf Docs](https://pypdf.readthedocs.io/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Prometheus Client Python](https://github.com/prometheus/client_python)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)

## Support

For issues, bugs, or feature requests, please open an issue on GitHub.