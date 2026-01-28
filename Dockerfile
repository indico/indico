FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential curl \
    libxslt1-dev libxml2-dev libffi-dev libpcre2-dev libyaml-dev \
    postgresql-client libpq-dev libjpeg62-turbo-dev zlib1g-dev libpango1.0-dev \
    git && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/indico

COPY requirements.txt requirements.dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements.dev.txt

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .
RUN pip install -e '.[dev]'

# Patch to disable URL validation for Docker
RUN sed -i 's/if url_root != config.BASE_URL:/if False and url_root != config.BASE_URL:/' /opt/indico/indico/web/flask/app.py

COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
