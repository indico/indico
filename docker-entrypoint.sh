#!/bin/bash
set -e

# Create necessary directories
mkdir -p /opt/indico/data/log /opt/indico/data/cache /opt/indico/data/tmp /opt/indico/data/archive

# Check if config exists
if [ ! -f /opt/indico/indico.conf ]; then
    echo "Creating default Indico configuration..."
    cat > /opt/indico/indico.conf <<EOF
SQLALCHEMY_DATABASE_URI = '${INDICO_DB_URI}'
REDIS_CACHE_URL = '${INDICO_REDIS_CACHE_URL}'
CELERY_BROKER = '${INDICO_REDIS_CACHE_URL}'
SECRET_KEY = 'changeme-docker-dev-key'
BASE_URL = 'http://localhost:8000'
ROUTE_OLD_URLS = True
STORAGE_BACKENDS = {'default': 'fs:/opt/indico/data/archive'}
TEMP_DIR = '/opt/indico/data/tmp'
CACHE_DIR = '/opt/indico/data/cache'
LOG_DIR = '/opt/indico/data/log'
LOGGING_CONFIG_FILE = '/opt/indico/logging-docker.yaml'
NO_REPLY_EMAIL = 'noreply@localhost'
SUPPORT_EMAIL = 'support@localhost'
DEBUG = True
EOF
fi

# Create simplified logging config for Docker
if [ ! -f /opt/indico/logging-docker.yaml ]; then
    cat > /opt/indico/logging-docker.yaml <<'EOF'
version: 1
root:
  level: INFO
  handlers: [console]
loggers:
  indico:
    handlers: [console]
  celery:
    handlers: [console]
handlers:
  console:
    class: logging.StreamHandler
    formatter: default
formatters:
  default:
    format: '%(asctime)s  %(levelname)-7s  %(name)-25s %(message)s'
EOF
fi

# Set config path
export INDICO_CONFIG=/opt/indico/indico.conf

# Wait for postgres
until PGPASSWORD=indico psql -h postgres -U indico -d indico -c '\q' 2>/dev/null; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

# Create extensions
echo "Creating PostgreSQL extensions..."
PGPASSWORD=indico psql -h postgres -U indico -d indico -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" || true
PGPASSWORD=indico psql -h postgres -U indico -d indico -c "CREATE EXTENSION IF NOT EXISTS unaccent;" || true

# Initialize database if needed
indico db prepare || true

# Build webpack assets if manifest doesn't exist
if [ ! -f /opt/indico/indico/web/static/dist/manifest.json ]; then
echo "Building webpack assets..."
cd /opt/indico
./bin/maintenance/build-assets.py indico --dev
fi

# Start Indico
exec indico run -h 0.0.0.0 -p 8000 -q --enable-evalex
