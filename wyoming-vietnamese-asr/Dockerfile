# Home Assistant Add-on: Wyoming Vietnamese ASR
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install system dependencies
RUN apk add --no-cache \
    ffmpeg \
    libsndfile \
    py3-numpy \
    py3-scipy

# Set working directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    wyoming==1.5.0 \
    soundfile==0.12.1 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    onnxruntime==1.16.3

# Copy application code
COPY server/ ./server/
COPY fastapi_server.py .

# Create model directory (data will be mounted)
RUN mkdir -p /data

# Copy run script
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# Expose ports
EXPOSE 10400 8090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(5); r = s.connect_ex(('127.0.0.1', 10400)); s.close(); exit(r)"

# Start server
CMD [ "/run.sh" ]
