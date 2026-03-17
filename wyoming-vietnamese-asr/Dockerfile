ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    ffmpeg \
    libsndfile

# Create app directory
WORKDIR /app

# Copy requirements and install
COPY wyoming-vietnamese-asr/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application
COPY wyoming-vietnamese-asr/server/ ./server/
COPY wyoming-vietnamese-asr/fastapi_server.py .

# Create model directory
RUN mkdir -p /data

# Copy run script
COPY wyoming-vietnamese-asr/run.sh /run.sh
RUN chmod a+x /run.sh

EXPOSE 10400 8090

CMD [ "/run.sh" ]
