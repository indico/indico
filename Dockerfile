# Main stage: Build Indico application
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential curl make git \
    libxslt1-dev libxml2-dev libffi-dev libpcre2-dev libyaml-dev \
    postgresql-client libpq-dev libjpeg62-turbo-dev zlib1g-dev libpango1.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/indico

# Install Python dependencies
COPY requirements.txt requirements.dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements.dev.txt build setuptools

# Install Node.js dependencies
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy application code and install
COPY . .
RUN pip install -e '.[dev]'

# Build webpack assets in production mode
RUN ./bin/maintenance/build-assets.py indico

# Copy entrypoint script
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
