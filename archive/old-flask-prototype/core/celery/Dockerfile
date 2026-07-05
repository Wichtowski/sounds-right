FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy only celery requirements
COPY app/core/celery/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the entire app directory
COPY app/ ./
# Set environment variables
ENV PYTHONPATH=/app

# Run Celery worker
CMD ["celery", "-A", "core.celery.app:app", "worker", "--loglevel=info"] 