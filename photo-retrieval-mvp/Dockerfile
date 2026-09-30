FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for Pillow, psycopg2, torch)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy application source first
COPY . .

# Install Python dependencies without editable mode
RUN pip install --no-cache-dir .

EXPOSE 8000

# Railway dynamically provides a PORT environment variable.
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
