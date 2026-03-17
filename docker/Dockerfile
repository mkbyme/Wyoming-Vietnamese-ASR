# Wyoming Vietnamese ASR - Docker Image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server/ ./server/
COPY fastapi_server.py .

# Create model directory (will be mounted at runtime)
RUN mkdir -p /app/model

# Expose ports
EXPOSE 10400 8090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(5); result = s.connect_ex(('localhost', 10400)); s.close(); exit(result)"

# Start Wyoming server (default)
CMD ["python", "server/main.py"]
