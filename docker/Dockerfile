# ============================================================
# STAGE 1: Builder
# ============================================================
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .

# sherpa-onnx==1.12.32 có pre-built wheel trên PyPI → không cần cmake
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================
# STAGE 2: Runtime
# ============================================================
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /install /usr/local

# ── Copy app files ────────────────────────────────────────────
COPY main.py            ./main.py
COPY healthcheck.py     ./healthcheck.py
COPY config.yaml        ./config/config.yaml

RUN mkdir -p /app/models /app/config \
    && useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

# ── Server config ─────────────────────────────────────────────
ENV SERVER_HOST="0.0.0.0" \
    SERVER_PORT="10400" \
    API_HOST="0.0.0.0" \
    API_PORT="8090" \
    LOG_LEVEL="INFO" \
    MODE="wyoming"

ENV CONFIG_FILE="/app/config/config.yaml"

# ── Model identity ────────────────────────────────────────────
# ENV MODEL_ID="zipformer-vietnamese-30m" \
#     MODEL_DISPLAY_NAME="Zipformer 30M RNNT Vietnamese" \
#     MODEL_DESCRIPTION="Zipformer-30M-RNNT-6000h - WER 7.97% on VLSP2025" \
#     MODEL_ATTRIBUTION_NAME="hynt" \
#     MODEL_ATTRIBUTION_URL="https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h" \
#     MODEL_LANGUAGES="vi"

# ENV HF_MODEL_ID="hynt/Zipformer-30M-RNNT-6000h" 

# ENV MODEL_DIR="/app/model"

# ENV ENCODER_FILE="encoder-epoch-20-avg-10.onnx" \
#     DECODER_FILE="decoder-epoch-20-avg-10.onnx" \
#     JOINER_FILE="joiner-epoch-20-avg-10.onnx" \
#     TOKENS_FILE="config.json"

# ENV REQUIRED_FILES=""

# ENV USE_INT8="false" \
#     NUM_THREADS="4" \
#     SAMPLE_RATE="16000" \
#     PROVIDER="cpu"

# ENV FORCE_DOWNLOAD="false"

EXPOSE 10400 8090

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=5 \
    CMD python /app/healthcheck.py

CMD ["python", "/app/main.py"]