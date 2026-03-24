# Wyoming Vietnamese ASR cho Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/gnolnos/wyoming-vietnamese-asr)](https://github.com/gnolnos/wyoming-vietnamese-asr/releases)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz/)
[![Docker](https://img.shields.io/docker/pulls/mkbyme/wyoming-vietnamese-asr)](https://hub.docker.com/r/mkbyme/wyoming-vietnamese-asr)

Tích hợp Nhận dạng Giọng nói Tiếng Việt (ASR) cho Home Assistant sử dụng giao thức Wyoming.

> 🇬🇧 **[Read English version](README.md)** | 🇻🇳 **[Bản tiếng Việt](README.vi.md)**

---

## ✨ Tính năng

- **ASR Tiếng Việt**: Nhận dạng giọng nói tiếng Việt độ chính xác cao (WER 7.97%)
- **Giao thức Wyoming**: Tích hợp trực tiếp với Wyoming STT của Home Assistant
- **Chế độ FastAPI**: REST API tùy chọn cho tích hợp bên ngoài (Xiaozhi, v.v.)
- **Điểm vào duy nhất**: Một file `main.py` xử lý cả Wyoming và FastAPI qua biến `MODE`
- **Cấu hình linh hoạt**: `config.yaml` (ưu tiên) → Biến môi trường (fallback)
- **Tự động tải model**: Model tự động tải từ HuggingFace khi khởi động lần đầu
- **Hỗ trợ Docker**: Triển khai độc lập với image tối ưu multi-stage

---

## 🧠 Các Model Hỗ Trợ

| Model | WER | Định dạng | Nguồn |
|---|---|---|---|
| **Zipformer-30M-RNNT-6000h** | 7.97% (VLSP2025) | ONNX FP32/INT8 | [hynt/Zipformer-30M-RNNT-6000h](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h) |
| **NghiASR** | — | ONNX | [NghiMe/NghiASR](https://huggingface.co/NghiMe/NghiASR) |

&gt; Mỗi model chạy trong **1 container riêng** với `MODEL_DIR` và `HF_MODEL_ID` tương ứng.



### Testing 

Hướng dẫn [kiểm tra dịch vụ](./test/README.md)
---

## 📦 Cài đặt

### HACS (Khuyến nghị)

1. Mở HACS trong Home Assistant
2. Tìm kiếm **"Wyoming Vietnamese ASR"**
3. Nhấn Cài đặt → Khởi động lại Home Assistant
4. Thêm tích hợp qua **Cài đặt → Thiết bị &amp; Dịch vụ**

### Thủ công

1. Tải bản phát hành mới nhất từ [GitHub Releases](https://github.com/gnolnos/wyoming-vietnamese-asr/releases)
2. Giải nén `wyoming_vietnamese.zip` vào `custom_components/wyoming_vietnamese/`
3. Khởi động lại Home Assistant → Thêm tích hợp qua giao diện

---

## ⚙️ Cấu hình

### Tích hợp Home Assistant

1. Vào **Cài đặt → Thiết bị &amp; Dịch vụ**
2. Nhấn **+ Thêm tích hợp** → Tìm **"Wyoming Vietnamese ASR"**
3. Cấu hình:
   - **Host**: IP của Wyoming server (ví dụ: `192.168.100.150`)
   - **Port**: Cổng Wyoming server (mặc định: `10400`)

### `config.yaml` (Khuyến nghị)

Mount `config.yaml` vào `/app/config/config.yaml` để override toàn bộ cấu hình.

#### Model 1: Zipformer-30M (mặc định)

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
  description: "Zipformer-30M-RNNT-6000h - WER 7.97% trên VLSP2025"
  attribution_name: "hynt"
  attribution_url: "https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h"
  languages:
    - "vi"

  hf_model_id: "hynt/Zipformer-30M-RNNT-6000h"
  hf_token: ""          # hoặc set qua biến môi trường HF_TOKEN

  model_dir: "/app/model"

  # Danh sách file cần xác minh + tải về nếu thiếu
  required_files:
    - "encoder-epoch-20-avg-10.onnx"
    - "decoder-epoch-20-avg-10.onnx"
    - "joiner-epoch-20-avg-10.onnx"
    - "config.json"

  encoder_file: "encoder-epoch-20-avg-10.onnx"
  decoder_file: "decoder-epoch-20-avg-10.onnx"
  joiner_file:  "joiner-epoch-20-avg-10.onnx"
  tokens_file:  "config.json"   # đổi thành "tokens.txt" nếu model khác dùng tên đó

  use_int8: false       # true = model INT8 quantized (nhẹ hơn ~2x)
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
  description: "NghiASR - Nhận dạng giọng nói tiếng Việt bởi NghiMe Studio"
  attribution_name: "NghiMe"
  attribution_url: "https://huggingface.co/NghiMe/NghiASR"
  languages:
    - "vi"

  hf_model_id: "NghiMe/NghiASR"
  hf_token: ""

  model_dir: "/app/model"

  # ⚠️ Xác minh tên file thực tế tại: https://huggingface.co/NghiMe/NghiASR/tree/main
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

### Biến Môi Trường (Fallback)

Tất cả field trong `config.yaml` đều có thể override bằng biến môi trường:

| Biến | Mặc định | Mô tả |
|---|---|---|
| `MODE` | `wyoming` | `wyoming` hoặc `fastapi` |
| `SERVER_PORT` | `10400` | Cổng Wyoming TCP |
| `API_PORT` | `8090` | Cổng FastAPI HTTP |
| `MODEL_ID` | `zipformer-vietnamese-30m` | ID hiển thị trong HASS |
| `MODEL_DIR` | `/app/model` | Thư mục chứa file model |
| `HF_MODEL_ID` | `hynt/Zipformer-30M-RNNT-6000h` | HuggingFace repo |
| `HF_TOKEN` | _(trống)_ | Token cho repo riêng tư |
| `TOKENS_FILE` | `config.json` | Tên file tokens |
| `REQUIRED_FILES` | _(tự động)_ | Danh sách file cần xác minh/tải (CSV) |
| `USE_INT8` | `false` | Dùng model INT8 quantized |
| `NUM_THREADS` | `4` | Số luồng CPU cho inference |
| `PROVIDER` | `cpu` | `cpu`, `cuda`, `coreml` |
| `FORCE_DOWNLOAD` | `false` | Tải lại dù file đã tồn tại |
| `CONFIG_FILE` | `/app/config/config.yaml` | Đường dẫn tới file config |

---

## 🐳 Triển khai Docker

### Cấu trúc thư mục

```
.
├── config/
│   └── config.yaml          # cấu hình runtime (mount từ host)
├── model/                   # file model (mount từ host)
│   ├── bpe.model
│   ├── config.json
│   ├── decoder-epoch-20-avg-10.onnx
│   ├── encoder-epoch-20-avg-10.onnx
│   └── joiner-epoch-20-avg-10.onnx
├── docker-compose.yaml
├── Dockerfile
├── main.py                  # điểm vào duy nhất (Wyoming + FastAPI)
├── healthcheck.py
├── config.yaml              # config mặc định baked-in
└── requirements.txt
```

### Chế độ Wyoming — 1 Model

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

  # ── Model 1: Zipformer 30M (cổng 10400) ──────────────────
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

  # ── Model 2: NghiASR (cổng 10401) ────────────────────────
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

### Chế độ FastAPI

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

&gt; **Lưu ý**: `sherpa-onnx` được cài từ pre-built wheel trên PyPI — **không cần cmake hay build tools** trong runtime.

---

## 🌐 Các Endpoint FastAPI

Khi `MODE=fastapi`, server expose các endpoint sau:

| Phương thức | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/health` | Kiểm tra trạng thái + metrics |
| `GET` | `/metrics` | Metrics tương thích Prometheus |
| `POST` | `/transcribe` | Upload audio → văn bản |

```bash
# Chuyển đổi file audio
curl -X POST "http://localhost:8090/transcribe" \
  -F "audio=@audio.wav"

# Kiểm tra trạng thái
curl http://localhost:8090/health
```

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────┐
│  Home Assistant (Trợ lý giọng nói)  │
│  Tích hợp Wyoming STT               │
└──────────────┬──────────────────────┘
               │ Giao thức Wyoming (TCP :10400)
               ▼
┌─────────────────────────────────────┐
│       main.py (điểm vào duy nhất)   │
│  MODE=wyoming → Wyoming Server      │
│  MODE=fastapi → FastAPI + uvicorn   │
│                                     │
│  Config: config.yaml &gt; ENV vars     │
│  Model: tự động tải từ HF           │
└──────────────┬──────────────────────┘
               │ (tùy chọn REST)
               ▼
┌─────────────────────────────────────┐
│  FastAPI Server (:8090)             │
│  /transcribe  /health  /metrics     │
└─────────────────────────────────────┘
```

---

## 🔧 Xử lý sự cố

### Container `unhealthy`

```bash
# Xem log healthcheck
docker inspect --format='{{json .State.Health}}' wyoming-vietnamese-asr | jq

# Xem log container
docker logs wyoming-vietnamese-asr --tail 50
```

&gt; **Lưu ý**: Lần đầu khởi động cần tải model (~200-500MB). `start-period=300s` được cấu hình để tránh báo unhealthy sai trong quá trình tải.

### Từ chối kết nối

- Kiểm tra container đang chạy: `docker ps | grep wyoming`
- Kiểm tra port binding: `docker port wyoming-vietnamese-asr`
- Kiểm tra quy tắc tường lửa

### Tải model thất bại

```bash
# Buộc tải lại
docker run -e FORCE_DOWNLOAD=true ...
# Hoặc set trong config.yaml: force_download: true
```

### Lỗi phân quyền (volume mount)

```bash
sudo chown -R 1000:1000 ./model ./config
```

### Xác minh danh sách file NghiASR

```bash
python -c "
from huggingface_hub import list_repo_files
for f in list_repo_files('NghiMe/NghiASR'):
    print(f)
"
```

Sau đó cập nhật `required_files` và các file roles trong `config.yaml` cho đúng tên file thực tế.

### Chất lượng nhận dạng kém

- Đảm bảo âm thanh đầu vào là tiếng Việt rõ ràng
- Kiểm tra cài đặt microphone trong Home Assistant
- Thử tăng `NUM_THREADS` nếu inference chậm

---

## 🛠️ Phát triển

```bash
# Build image
docker build -t wyoming-vietnamese-asr .

# Chạy chế độ Wyoming
docker run -p 10400:10400 -v ./model:/app/model wyoming-vietnamese-asr

# Chạy chế độ FastAPI
docker run -p 8090:8090 -e MODE=fastapi -v ./model:/app/model wyoming-vietnamese-asr

# Chạy tests
python -m pytest tests/
```

---

## 📄 Giấy phép

Giấy phép MIT — Xem [LICENSE](LICENSE) để biết chi tiết.

---

## 🙏 Ghi công

- **Model 1**: [hynt/Zipformer-30M-RNNT-6000h](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h)
- **Model 2**: [NghiMe/NghiASR](https://huggingface.co/NghiMe/NghiASR)
- **Giao thức Wyoming**: [Home Assistant](https://www.home-assistant.io/integrations/wyoming/)
- **ASR Engine**: [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)
- **Tích hợp**: [gnolnos](https://github.com/gnolnos)
