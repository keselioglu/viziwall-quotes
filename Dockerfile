# --- Frontend build ---
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
# Same-origin deploy: frontend and API share admin.viziwall.com, so the API is just /api.
ENV VITE_API_URL=/api
RUN npm run build

# --- Backend runtime ---
# Pinned to Debian 12 (bookworm) rather than the floating "slim" tag: it recently moved to
# trixie, where libgdk-pixbuf2.0-0 was renamed to libgdk-pixbuf-2.0-0 and broke this build.
# Pinning avoids chasing renamed packages again on the next base-image update.
FROM python:3.12-slim-bookworm AS backend

# WeasyPrint (backend/app/pdf.py) needs these native libs at runtime — without them the
# PDF endpoint 500s even though everything else works. See:
# https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#debian-ubuntu
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev \
    libjpeg62-turbo \
    shared-mime-info \
    fontconfig \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
COPY --from=frontend-build /app/frontend/dist ./static

COPY docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

# Railway injects PORT at runtime; 8000 is only a local-run fallback.
ENV PORT=8000
EXPOSE 8000

CMD ["./docker-entrypoint.sh"]
