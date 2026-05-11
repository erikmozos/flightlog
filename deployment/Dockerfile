FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=flightlog.settings \
    DJANGO_DEBUG=0 \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,web

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ARG DJANGO_SECRET_KEY=docker-build-only-not-for-production
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}

RUN mkdir -p /app/staticfiles

RUN DJANGO_SERVE_MEDIA=0 DJANGO_SECRET_KEY=docker-build-static python manage.py collectstatic --noinput \
    --clear

COPY deployment/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
