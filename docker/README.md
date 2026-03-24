# Wyoming Vietnamese ASR cho Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/gnolnos/wyoming-vietnamese-asr)](https://github.com/gnolnos/wyoming-vietnamese-asr/releases)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz/)
[![Docker](https://img.shields.io/docker/pulls/mkbyme/wyoming-vietnamese-asr)](https://hub.docker.com/r/mkbyme/wyoming-vietnamese-asr)

Vietnamese Automatic Speech Recognition (ASR) integration for Home Assistant using Wyoming protocol.

> 🇻🇳 **[Đọc bản tiếng Việt](README.vi.md)** | **[English version](README.md)**

---

## ✨ Features

- **Vietnamese ASR**: High-accuracy Vietnamese speech recognition
- **Wyoming Protocol**: Native integration with Home Assistant's Wyoming STT
- **FastAPI Mode**: Optional REST API for external integrations (Xiaozhi, etc.)
- **Single Entry Point**: One `main.py` handles both Wyoming and FastAPI modes via `MODE` env
- **Flexible Config**: `config.yaml` (priority) → Environment Variables (fallback)
- **Auto-Download**: Model auto-downloaded from HuggingFace on first start
- **Docker Support**: Standalone deployment with multi-stage optimized image

---

## 🧠 Supported Models

| Model | WER | Format | Source |
|---|---|---|---|
| **Zipformer-30M-RNNT-6000h** | 7.97% (VLSP2025) | ONNX FP32/INT8 | [hynt/Zipformer-30M-RNNT-6000h](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h) |
| **NghiASR** | — | ONNX | [NghiMe/NghiASR](https://huggingface.co/NghiMe/NghiASR) |

&gt; Mỗi model chạy trong **1 container riêng** với `MODEL_DIR` và `HF_MODEL_ID` tương ứng.

---

## 📦 Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Search for **"Wyoming Vietnamese ASR"**
3. Click Install → Restart Home Assistant
4. Add integration via **Settings → Devices &amp; Services**

### Manual

1. Download the latest release from [GitHub Releases](https://github.com/gnolnos/wyoming-vietnamese-asr/releases)
2. Extract `wyoming_vietnamese.zip` to `custom_components/wyoming_vietnamese/`
3. Restart Home Assistant → Add integration via UI

---

### Testing 

Check at [Testing Guide](./test/README.md)

## ⚙️ Configuration

### Home Assistant Integration

1. Go to **Settings → Devices &amp; Services**
2. Click **+ Add Integration** → Search **"Wyoming Vietnamese ASR"**
3. Configure:
   - **Host**: Wyoming server IP (e.g. `192.168.100.150`)
   - **Port**: Wyoming server port (default: `10400`)

### `config.yaml` (Recommended)

Mount `config.yaml` vào `/app/config/config.yaml` để override toàn bộ cấu hình.

#### Model 1: Zipformer-30M (default)

```yaml
# config.yaml — Zipformer 30M
server:
  host: "0.0.0.0"
  port: 10400
  api_host: "0.0.0.0"
  api_port: 8090
  log_level: "INFO"    # DEBUG | INFO | WARNING | ERROR
  mode: "wyoming"      # wyoming | fastapi

model:
  id: "zipformer-vietnamese-30m"
  display_name: "Zipformer 30M RNNT Vietnamese"
  description: "Zipformer-30M-RNNT-6000h - WER 7.97% on VLSP2025"
  attribution_name: "hynt"
  attribution_url: "https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h"
  languages:
    - "vi"

  hf_model_id: "hynt/Zipformer-30M-RNNT-6000h"
  hf_token: ""          # hoặc set qua env HF_TOKEN

  model_dir: "/app/model"

  required_files:
    - "encoder-epoch-20-avg-10.onnx"
    - "decoder-epoch-20-avg-10.onnx"
    - "joiner-epoch-20-avg-10.onnx"
    - "config.json"

  encoder_file: "encoder-epoch-20-avg-10.onnx"
  decoder_file: "decoder-epoch-20-avg-10.onnx"
  joiner_file:  "joiner-epoch-20-avg-10.onnx"
  tokens_file:  "config.json"   # đổi thành "tokens.txt" nếu model khác

  use_int8: false       # true = INT8 quantized (~2x nhẹ hơn)
  num_threads: 4
  sample_rate: 16000
  provider: "cpu"       # cpu | cuda | coreml
  force_download: false
```

#### Model 2: NghiASR

```yaml
# config.yaml — NghiASR
server:
  host: "0.0.0.0"
  port: 10401
  api_host: "0.0.0.0"
  api_port: 8091
  log_level: "INFO"
  mode: "wyoming"

model:
  id: "nghime-asr"
  display_name: "NghiMe NghiASR Vietnamese"
  description: "NghiASR - Vietnamese ASR by NghiMe Studio"
  attribution_name: "NghiMe"
  attribution_url: "https://huggingface.co/NghiMe/NghiASR"
  languages:
    - "vi"

  hf_model_id: "NghiMe/NghiASR"
  hf_token: ""

  model_dir: "/app/model"

  # ⚠️ Verify tên file thực tế tại: https://huggingface.co/NghiMe/NghiASR/tree/main
  required_files:
    - "encoder-epoch-4-avg-4.onnx"
    - "decoder-epoch-4-avg-4.onnx"
    - "joiner-epoch-4-avg-4.onnx"
    - "tokens.txt"

  encoder_file: "encoder-epoch-4-avg-4.onnx"
  decoder_file: "decoder-epoch-4-avg-4.onnx"
  joiner_file:  "joiner-epoch-4-avg-4.onnx"
  tokens_file:  "tokens.txt"

  use_int8: false
  num_threads: 4
  sample_rate: 16000
  provider: "cpu"
  force_download: false
```

### Environment Variables (Fallback)

Tất cả field trong `config.yaml` đều có thể override bằng env vars:

| ENV | Default | Mô tả |
|---|---|---|
| `MODE` | `wyoming` | `wyoming` hoặc `fastapi` |
| `SERVER_PORT` | `10400` | Wyoming TCP port |
| `API_PORT` | `8090` | FastAPI HTTP port |
| `MODEL_ID` | `zipformer-vietnamese-30m` | ID expose ra HASS |
| `MODEL_DIR` | `/app/model` | Thư mục chứa model files |
| `HF_MODEL_ID` | `hynt/Zipformer-30M-RNNT-6000h` | HuggingFace repo |
| `HF_TOKEN` | _(empty)_ | Token cho private repo |
| `TOKENS_FILE` | `config.json` | Tên file tokens |
| `REQUIRED_FILES` | _(auto)_ | CSV list file cần verify/download |
| `USE_INT8` | `false` | Dùng INT8 quantized model |
| `NUM_THREADS` | `4` | CPU threads cho inference |
| `PROVIDER` | `cpu` | `cpu`, `cuda`, `coreml` |
| `FORCE_DOWNLOAD` | `false` | Re-download dù file đã có |
| `CONFIG_FILE` | `/app/config/config.yaml` | Path tới config file |

---

## 🐳 Docker Deployment

### Project Structure

```
.
├── config/
│   └── config.yaml          # runtime config (mount từ host)
├── model/                   # model files (mount từ host)
│   ├── bpe.model
│   ├── config.json
│   ├── decoder-epoch-20-avg-10.onnx
│   ├── encoder-epoch-20-avg-10.onnx
│   └── joiner-epoch-20-avg-10.onnx
├── docker-compose.yaml
├── Dockerfile
├── main.py                  # single entry point (Wyoming + FastAPI)
├── healthcheck.py
├── config.yaml              # baked-in default config
└── requirements.txt
```

### Wyoming Mode — Single Model

```yaml
services:
  wyoming-asr:
    build: .
    container_name: wyoming-vietnamese-asr
    restart: unless-stopped
    environment:
      MODE: "wyoming"
      MODEL_DIR: "/app/model"
      HF_MODEL_ID: "hynt/Zipformer-30M-RNNT-6000h"
      NUM_THREADS: "4"
      FORCE_DOWNLOAD: "false"
    ports:
      - "10400:10400"
    volumes:
      - ./model:/app/model
      - ./config:/app/config
```

### Chạy 2 Model Song Song

```yaml
services:

  # ── Model 1: Zipformer 30M (port 10400) ──────────────────
  wyoming-zipformer:
    build: .
    container_name: wyoming-zipformer-30m
    restart: unless-stopped
    environment:
      MODE: "wyoming"
      MODEL_ID: "zipformer-vietnamese-30m"
      MODEL_DISPLAY_NAME: "Zipformer 30M RNNT Vietnamese"
      HF_MODEL_ID: "hynt/Zipformer-30M-RNNT-6000h"
      MODEL_DIR: "/app/model"
      NUM_THREADS: "4"
    ports:
      - "10400:10400"
    volumes:
      - ./model:/app/model
      - ./config:/app/config

  # ── Model 2: NghiASR (port 10401) ────────────────────────
  wyoming-nghiasr:
    build: .
    container_name: wyoming-nghiasr
    restart: unless-stopped
    environment:
      MODE: "wyoming"
      SERVER_PORT: "10401"
      MODEL_ID: "nghime-asr"
      MODEL_DISPLAY_NAME: "NghiMe NghiASR Vietnamese"
      MODEL_ATTRIBUTION_NAME: "NghiMe"
      MODEL_ATTRIBUTION_URL: "https://huggingface.co/NghiMe/NghiASR"
      HF_MODEL_ID: "NghiMe/NghiASR"
      MODEL_DIR: "/app/model"
      NUM_THREADS: "4"
    ports:
      - "10401:10401"
    volumes:
      - ./model-nghiasr:/app/model   # volume riêng, tránh conflict
      - ./config-nghiasr:/app/config
```

### FastAPI Mode

```yaml
services:
  fastapi-asr:
    build: .
    container_name: vietnamese-asr-api
    restart: unless-stopped
    environment:
      MODE: "fastapi"
      API_PORT: "8090"
      MODEL_DIR: "/app/model"
    ports:
      - "8090:8090"
    volumes:
      - ./model:/app/model
      - ./config:/app/config
```

### Build Image

```bash
docker build -t wyoming-vietnamese-asr .
```

&gt; **Note**: `sherpa-onnx` được install từ pre-built wheel trên PyPI — **không cần cmake hay build tools** trong runtime.

---

## 🌐 FastAPI Endpoints

Khi `MODE=fastapi`, server expose các endpoint:

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/health` | Health check + metrics |
| `GET` | `/metrics` | Prometheus-compatible metrics |
| `POST` | `/transcribe` | Upload audio → text |

```bash
# Transcribe audio file
curl -X POST "http://localhost:8090/transcribe" \
  -F "audio=@audio.wav"

# Health check
curl http://localhost:8090/health
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│  Home Assistant (Voice Assistant)   │
│  Wyoming STT Integration            │
└──────────────┬──────────────────────┘
               │ Wyoming Protocol (TCP :10400)
               ▼
┌─────────────────────────────────────┐
│         main.py (single entry)      │
│  MODE=wyoming → Wyoming Server      │
│  MODE=fastapi → FastAPI + uvicorn   │
│                                     │
│  Config: config.yaml &gt; ENV vars     │
│  Model: auto-download from HF       │
└──────────────┬──────────────────────┘
               │ (optional REST)
               ▼
┌─────────────────────────────────────┐
│  FastAPI Server (:8090)             │
│  /transcribe  /health  /metrics     │
└─────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Container `unhealthy`

```bash
# Xem healthcheck log
docker inspect --format='{{json .State.Health}}' wyoming-vietnamese-asr | jq

# Xem container logs
docker logs wyoming-vietnamese-asr --tail 50
```

&gt; **Lưu ý**: Lần đầu start cần download model (~200-500MB). `start-period=300s` được set để tránh false unhealthy trong quá trình download.

### Connection Refused

- Kiểm tra container đang chạy: `docker ps | grep wyoming`
- Kiểm tra port binding: `docker port wyoming-vietnamese-asr`
- Kiểm tra firewall rules

### Model Download Fail

```bash
# Force re-download
docker run -e FORCE_DOWNLOAD=true ...
# Hoặc set trong config.yaml: force_download: true
```

### Permission Denied (volume mount)

```bash
sudo chown -R 1000:1000 ./model ./config
```

### Verify NghiASR File List

```bash
python -c "
from huggingface_hub import list_repo_files
for f in list_repo_files('NghiMe/NghiASR'):
    print(f)
"
```

Sau đó cập nhật `required_files` và file roles trong `config.yaml` cho đúng tên file thực tế.

---

## 🛠️ Development

```bash
# Build image
docker build -t wyoming-vietnamese-asr .

# Run Wyoming mode
docker run -p 10400:10400 -v ./model:/app/model wyoming-vietnamese-asr

# Run FastAPI mode
docker run -p 8090:8090 -e MODE=fastapi -v ./model:/app/model wyoming-vietnamese-asr

# Run tests
python -m pytest tests/
```

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 🙏 Credits

- **Model 1**: [hynt/Zipformer-30M-RNNT-6000h](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h)
- **Model 2**: [NghiMe/NghiASR](https://huggingface.co/NghiMe/NghiASR)
- **Wyoming Protocol**: [Home Assistant](https://www.home-assistant.io/integrations/wyoming/)
- **ASR Engine**: [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)
- **Integration**: [gnolnos](https://github.com/gnolnos)