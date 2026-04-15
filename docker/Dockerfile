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
        libsndfile1 ffmpeg curl tzdata \
    && ln -sf /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime \
    && echo "Asia/Ho_Chi_Minh" > /etc/timezone \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ──────────────────────────────────────────────
# BASE: CUDA12 — runtime only
# ──────────────────────────────────────────────
FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04 AS base-cuda12

ENV DEBIAN_FRONTEND=noninteractive TZ=Asia/Ho_Chi_Minh

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip \
        libsndfile1 ffmpeg curl tzdata \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && ln -sf /usr/bin/pip3    /usr/bin/pip \
    && ln -sf /usr/share/zoneinfo/Asia/Ho_Chi_Minh /etc/localtime \
    && echo "Asia/Ho_Chi_Minh" > /etc/timezone \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ──────────────────────────────────────────────
# BUILDER: CPU
# ──────────────────────────────────────────────
FROM python:3.11-slim AS builder-cpu

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements-cpu.txt requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ──────────────────────────────────────────────
# BUILDER: CUDA12
# ──────────────────────────────────────────────
FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04 AS builder-cuda12

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev \
        build-essential git curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements-cuda12.txt requirements.txt

RUN pip install --no-cache-dir --break-system-packages --target=/install -r requirements.txt \
    && SHERPA_SITE="/install/lib/python$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages/sherpa_onnx" \
    && echo "📦 Downloading sherpa-onnx GPU .so → ${SHERPA_SITE}" \
    && mkdir -p /tmp/sherpa-gpu \
    && curl -fL "https://github.com/k2-fsa/sherpa-onnx/releases/download/v1.12.32/sherpa-onnx-v1.12.32-cuda-12.x-cudnn-9.x-linux-x64-gpu.tar.bz2" \
       | tar -xj -C /tmp/sherpa-gpu \
    && find /tmp/sherpa-gpu -name "*.so*" -exec cp -v {} "${SHERPA_SITE}/" \; \
    && rm -rf /tmp/sherpa-gpu \
    && echo "✅ GPU .so override done"

# ──────────────────────────────────────────────
# Intermediate alias — bypass --from ARG limitation
# ──────────────────────────────────────────────
FROM builder-${VARIANT} AS builder-selected

# ──────────────────────────────────────────────
# RUNTIME: unified
# ──────────────────────────────────────────────
FROM base-${VARIANT} AS runtime

ARG VARIANT=cpu

# ✅ Chỉ copy /install — không kéo build tools vào runtime
COPY --from=builder-selected /install /usr/local

ARG PYTHONPATH=""
ENV PYTHONPATH="/usr/local/lib/python3.12/site-packages:/usr/local/lib/python3.11/site-packages:${PYTHONPATH}"

WORKDIR /app
COPY main.py         ./main.py
COPY healthcheck.py  ./healthcheck.py
COPY config.yaml     ./config/config.yaml

RUN mkdir -p /app/models /app/config

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
