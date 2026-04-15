# ══════════════════════════════════════════════
# ARG VARIANT: cpu (default) | cuda12
# ══════════════════════════════════════════════
ARG VARIANT=cpu

# ──────────────────────────────────────────────
# BASE: CPU (amd64 + arm64)
# ──────────────────────────────────────────────
FROM python:3.11-slim AS base-cpu

ENV DEBIAN_FRONTEND=noninteractive TZ=Asia/Ho_Chi_Minh

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git \
        libsndfile1 ffmpeg curl tzdata \
    && ln -sf /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime \
    && echo "Asia/Ho_Chi_Minh" > /etc/timezone \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ──────────────────────────────────────────────
# BASE: CUDA 12 (amd64 only)
# ──────────────────────────────────────────────
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 AS base-cuda12

ENV DEBIAN_FRONTEND=noninteractive TZ=Asia/Ho_Chi_Minh

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-dev python3-pip \
        build-essential git \
        libsndfile1 ffmpeg curl tzdata \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3    /usr/bin/python \
    && ln -sf /usr/bin/pip3       /usr/bin/pip \
    && ln -sf /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime \
    && echo "Asia/Ho_Chi_Minh" > /etc/timezone \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ──────────────────────────────────────────────
# BUILDER: install deps vào /install
# ──────────────────────────────────────────────
FROM base-${VARIANT} AS builder

ARG VARIANT=cpu          # ✅ Re-declare trong stage này

WORKDIR /build

# Copy requirements theo variant
COPY requirements-${VARIANT}.txt requirements.txt

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ──────────────────────────────────────────────
# RUNTIME: final image
# ──────────────────────────────────────────────
FROM base-${VARIANT} AS runtime

ARG VARIANT=cpu          # ✅ Re-declare nếu cần dùng VARIANT trong stage này

WORKDIR /app

# Copy installed packages từ builder
COPY --from=builder /install /usr/local

# Copy app
COPY main.py         ./main.py
COPY healthcheck.py  ./healthcheck.py
COPY config.yaml     ./config/config.yaml

RUN mkdir -p /app/models /app/config \
    && useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

# ── Server ENV ────────────────────────────────
ENV SERVER_HOST="0.0.0.0" \
    SERVER_PORT="10400"    \
    API_HOST="0.0.0.0"     \
    API_PORT="8090"        \
    LOG_LEVEL="INFO"       \
    MODE="wyoming"         \
    CONFIG_FILE="/app/config/config.yaml"

EXPOSE 10400 8090

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=5 \
    CMD python /app/healthcheck.py

CMD ["python", "/app/main.py"]
