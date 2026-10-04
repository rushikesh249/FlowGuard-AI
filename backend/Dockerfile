# ── FlowGuard AI — Backend Dockerfile ──────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for PM4Py / numpy / psycopg2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
        graphviz \
        libgraphviz-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p /app/datasets/raw /app/datasets/cleaned \
             /app/ai/models /app/ai/results

# Make entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
