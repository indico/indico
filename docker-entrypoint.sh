#!/bin/bash
set -e

POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-indico}

# Create directories
mkdir -p /opt/indico/data/{log,cache,tmp,archive}

# Create Indico configuration
if [ ! -f /opt/indico/indico.conf ]; then
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
SMTP_SERVER = ('${INDICO_SMTP_SERVER}', ${INDICO_SMTP_PORT})
SMTP_USE_TLS = False
DEBUG = True
EOF
fi

# Create logging configuration
if [ ! -f /opt/indico/logging-docker.yaml ]; then
    cat > /opt/indico/logging-docker.yaml <<'EOF'
version: 1
root:
  level: INFO
  handlers: [console]
loggers:
  indico:
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

export INDICO_CONFIG=/opt/indico/indico.conf

# Wait for PostgreSQL
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U indico -d indico -c '\q' 2>/dev/null; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

# Initialize database
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U indico -d indico -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" 2>/dev/null || true
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U indico -d indico -c "CREATE EXTENSION IF NOT EXISTS unaccent;" 2>/dev/null || true
indico db prepare || true

echo "Starting Indico without instrumentation..."
exec python3 -c "
from indico.web.flask.app import make_app
app = make_app()
app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)
"
