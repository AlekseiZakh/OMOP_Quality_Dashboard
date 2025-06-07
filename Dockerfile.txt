# Multi-stage Docker build for OMOP Quality Dashboard

# Build argument for Python version
ARG PYTHON_VERSION=3.11

# =============================================================================
# Stage 1: Build dependencies and compile Python packages
# =============================================================================
FROM python:${PYTHON_VERSION}-slim as builder

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

# Labels for image metadata
LABEL maintainer="OMOP Quality Dashboard Team"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.version=$VERSION
LABEL org.label-schema.name="OMOP Quality Dashboard"
LABEL org.label-schema.description="Comprehensive data quality monitoring for OMOP CDM"
LABEL org.label-schema.schema-version="1.0"

# Set build environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    unixodbc-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install wheel
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# =============================================================================
# Stage 2: Runtime image
# =============================================================================
FROM python:${PYTHON_VERSION}-slim as runtime

# Runtime environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    unixodbc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r omop && useradd -r -g omop -u 1001 omop

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/exports /app/data /app/config \
    && chown -R omop:omop /app

# Copy application files
COPY --chown=omop:omop app/ ./app/
COPY --chown=omop:omop config.yaml ./
COPY --chown=omop:omop run_dashboard.py ./
COPY --chown=omop:omop .env.example ./

# Copy additional configuration files if they exist
COPY --chown=omop:omop config/ ./config/ 2>/dev/null || :

# Create health check script
RUN echo '#!/bin/bash\ncurl -f http://localhost:8501/_stcore/health || exit 1' > /app/healthcheck.sh \
    && chmod +x /app/healthcheck.sh \
    && chown omop:omop /app/healthcheck.sh

# Switch to non-root user
USER omop

# Expose the application port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD ["/app/healthcheck.sh"]

# Default command
CMD ["python", "run_dashboard.py", "--host", "0.0.0.0", "--no-browser"]

# =============================================================================
# Stage 3: Development image (optional)
# =============================================================================
FROM runtime as development

# Switch back to root for installing dev dependencies
USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    black \
    flake8 \
    mypy \
    jupyter

# Create development directories
RUN mkdir -p /app/tests /app/notebooks \
    && chown -R omop:omop /app

# Switch back to omop user
USER omop

# Development command with auto-reload
CMD ["python", "run_dashboard.py", "--debug", "--host", "0.0.0.0", "--no-browser"]

# =============================================================================
# Build hooks and metadata
# =============================================================================

# Build-time metadata as defined at http://label-schema.org
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="OMOP Quality Dashboard" \
      org.label-schema.description="Comprehensive data quality monitoring dashboard for OMOP Common Data Model" \
      org.label-schema.url="https://github.com/your-org/omop-quality-dashboard" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/your-org/omop-quality-dashboard" \
      org.label-schema.vendor="Your Organization" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

---

# .dockerignore
# Exclude files and directories from Docker build context

# Git
.git/
.gitignore
.gitattributes

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff
*.log
local_settings.py
db.sqlite3

# Flask stuff
instance/
.webassets-cache

# Scrapy stuff
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.env.*
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
logs/
exports/
backups/
data/
*.db
*.sqlite
*.sqlite3

# Docker
Dockerfile*
docker-compose*.yml
.dockerignore

# Documentation
README.md
CHANGELOG.md
docs/

# CI/CD
.github/
.gitlab-ci.yml
.travis.yml
Jenkinsfile

# Configuration (will be mounted as volumes)
config.yaml

# Tests (not needed in production image)
tests/
conftest.py
pytest.ini

# Development tools
Makefile
requirements-test.txt

---

# docker-entrypoint.sh
#!/bin/bash
# Docker entrypoint script for OMOP Quality Dashboard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Function to wait for database
wait_for_db() {
    local db_host="${OMOP_DB_HOST:-localhost}"
    local db_port="${OMOP_DB_PORT:-5432}"
    local max_attempts=30
    local attempt=1
    
    log "Waiting for database at ${db_host}:${db_port}..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$db_host" "$db_port" 2>/dev/null; then
            log "Database is available!"
            return 0
        fi
        
        warn "Database not available yet (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    error "Database is not available after $max_attempts attempts"
    return 1
}

# Function to validate environment
validate_environment() {
    log "Validating environment..."
    
    # Check required environment variables
    local required_vars=("OMOP_DB_TYPE" "OMOP_DB_HOST" "OMOP_DB_NAME")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        error "Missing required environment variables: ${missing_vars[*]}"
        return 1
    fi
    
    # Validate database type
    local db_type="${OMOP_DB_TYPE}"
    if [[ ! "$db_type" =~ ^(postgresql|sqlserver|sqlite)$ ]]; then
        error "Invalid database type: $db_type. Must be postgresql, sqlserver, or sqlite"
        return 1
    fi
    
    log "Environment validation passed"
    return 0
}

# Function to setup directories
setup_directories() {
    log "Setting up directories..."
    
    local dirs=("logs" "exports" "data" "config")
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "/app/$dir" ]; then
            mkdir -p "/app/$dir"
            log "Created directory: /app/$dir"
        fi
    done
}

# Function to initialize configuration
init_config() {
    log "Initializing configuration..."
    
    # Copy default config if it doesn't exist
    if [ ! -f "/app/config.yaml" ] && [ -f "/app/config.yaml.example" ]; then
        cp "/app/config.yaml.example" "/app/config.yaml"
        log "Created config.yaml from example"
    fi
    
    # Create .env from .env.example if it doesn't exist
    if [ ! -f "/app/.env" ] && [ -f "/app/.env.example" ]; then
        cp "/app/.env.example" "/app/.env"
        log "Created .env from example"
    fi
}

# Function to run health checks
health_check() {
    log "Running health checks..."
    
    # Check Python dependencies
    python -c "import streamlit, pandas, plotly, sqlalchemy" || {
        error "Required Python packages are not installed"
        return 1
    }
    
    # Check application structure
    local required_files=("app/main.py" "app/__init__.py")
    
    for file in "${required_files[@]}"; do
        if [ ! -f "/app/$file" ]; then
            error "Required file not found: $file"
            return 1
        fi
    done
    
    log "Health checks passed"
    return 0
}

# Main execution
main() {
    log "Starting OMOP Quality Dashboard..."
    
    # Setup
    setup_directories
    init_config
    
    # Validation
    validate_environment || exit 1
    health_check || exit 1
    
    # Wait for database if not SQLite
    if [ "${OMOP_DB_TYPE}" != "sqlite" ]; then
        wait_for_db || exit 1
    fi
    
    log "Initialization complete. Starting application..."
    
    # Execute the main command
    exec "$@"
}

# Handle signals
trap 'log "Received SIGTERM, shutting down gracefully..."; exit 0' TERM
trap 'log "Received SIGINT, shutting down gracefully..."; exit 0' INT

# Run main function if script is executed directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
