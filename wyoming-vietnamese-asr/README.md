# Wyoming Vietnamese ASR Add-on

Vietnamese Automatic Speech Recognition for Home Assistant.

## Features

- 🇻🇳 Vietnamese ASR (WER 7.97%)
- 🔌 Wyoming protocol integration
- 🐳 Docker container
- ⚡ Real-time speech recognition

## Configuration

```yaml
wyoming_vietnamese_asr:
  embedding_model: qwen3-embedding:4b
  log_level: info
```

## Usage

1. Install add-on
2. Start add-on
3. Go to Settings → Devices & Services
4. Add Wyoming integration pointing to `localhost:10400`
