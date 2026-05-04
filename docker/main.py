#!/usr/bin/env python3
"""
Wyoming + FastAPI ASR Server - Single Entry Point
MODE=wyoming  → Wyoming protocol (default, for Home Assistant)
MODE=fastapi  → REST API (for direct HTTP access)
Config priority: ENV vars > config.yaml > defaults
"""

import asyncio
import fcntl
import logging
import os
import tempfile
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np
import sherpa_onnx

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _normalize_text(text: str) -> str:
    """Convert ASR output to proper casing and suppress noise during silence"""
    text = text.strip()
    if len(text) < 5:
        return ""
    return text.capitalize()

def _get_bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(default)).lower() in ("1", "true", "yes")

def _get_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default

def _get_list(key: str, default: List[str]) -> List[str]:
    val = os.environ.get(key, "")
    return [v.strip() for v in val.split(",") if v.strip()] if val else default

# ─────────────────────────────────────────────
# Logging (early init, re-apply sau load_config)
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_LOGGER = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# ModelConfig
# ─────────────────────────────────────────────
@dataclass
class ModelConfig:
    # Identity
    id: str
    display_name: str
    description: str
    attribution_name: str
    attribution_url: str
    languages: List[str]

    # HuggingFace
    hf_model_id: str
    hf_token: Optional[str]

    # Storage
    model_dir: Path
    required_files: List[str]

    # File roles
    encoder_file: str
    decoder_file: str
    joiner_file: str
    tokens_file: str

    # Runtime
    use_int8: bool
    num_threads: int
    sample_rate: int
    provider: str
    force_download: bool

    # Loaded recognizer (runtime only)
    recognizer: Optional[object] = field(default=None, repr=False)

    @property
    def encoder_path(self) -> Path: return self.model_dir / self.encoder_file
    @property
    def decoder_path(self) -> Path: return self.model_dir / self.decoder_file
    @property
    def joiner_path(self)  -> Path: return self.model_dir / self.joiner_file
    @property
    def tokens_path(self)  -> Path: return self.model_dir / self.tokens_file


# ─────────────────────────────────────────────
# Config Loader
# ─────────────────────────────────────────────
CONFIG_FILE = Path(os.environ.get("CONFIG_FILE", "/app/config/config.yaml"))

def _env_fallback() -> tuple[dict, ModelConfig]:
    use_int8     = _get_bool("USE_INT8", False)
    suffix       = ".int8.onnx" if use_int8 else ".onnx"
    base         = "epoch-20-avg-10"
    hf_model_id  = os.environ.get("HF_MODEL_ID", "hynt/Zipformer-30M-RNNT-6000h")

    encoder_file = os.environ.get("ENCODER_FILE", f"encoder-{base}{suffix}")
    decoder_file = os.environ.get("DECODER_FILE", f"decoder-{base}{suffix}")
    joiner_file  = os.environ.get("JOINER_FILE",  f"joiner-{base}{suffix}")
    tokens_file  = os.environ.get("TOKENS_FILE",  "config.json")

    req_env        = _get_list("REQUIRED_FILES", [])
    required_files = req_env or [encoder_file, decoder_file, joiner_file, tokens_file]

    server_cfg = {
        "host":      os.environ.get("SERVER_HOST", "0.0.0.0"),
        "port":      _get_int("SERVER_PORT", 10400),
        "api_host":  os.environ.get("API_HOST", "0.0.0.0"),
        "api_port":  _get_int("API_PORT", 8090),
        "log_level": os.environ.get("LOG_LEVEL", "INFO").upper(),
        "mode":      os.environ.get("MODE", "wyoming").lower(),
    }

    model_cfg = ModelConfig(
        id               = os.environ.get("MODEL_ID", "default-asr"),
        display_name     = os.environ.get("MODEL_DISPLAY_NAME", "Vietnamese ASR"),
        description      = os.environ.get("MODEL_DESCRIPTION", "Vietnamese ASR Model"),
        attribution_name = os.environ.get("MODEL_ATTRIBUTION_NAME",                                        hf_model_id.split("/")[0]),
        attribution_url  = os.environ.get("MODEL_ATTRIBUTION_URL",                                        f"https://huggingface.co/{hf_model_id}"),
        languages        = _get_list("MODEL_LANGUAGES", ["vi"]),
        hf_model_id      = hf_model_id,
        hf_token         = os.environ.get("HF_TOKEN") or None,
        model_dir        = Path(os.environ.get("MODEL_DIR", "/app/model")),
        required_files   = required_files,
        encoder_file     = encoder_file,
        decoder_file     = decoder_file,
        joiner_file      = joiner_file,
        tokens_file      = tokens_file,
        use_int8         = use_int8,
        num_threads      = _get_int("NUM_THREADS", 4),
        sample_rate      = _get_int("SAMPLE_RATE", 16000),
        provider         = os.environ.get("PROVIDER", "cpu"),
        force_download   = _get_bool("FORCE_DOWNLOAD", False),
    )
    return server_cfg, model_cfg


def load_config() -> tuple[dict, ModelConfig]:
    if not CONFIG_FILE.exists():
        _LOGGER.info("📌 No config.yaml → using environment variables")
        return _env_fallback()

    _LOGGER.info(f"📄 Loading config: {CONFIG_FILE}")
    try:
        import yaml
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except Exception as e:
        _LOGGER.error(f"❌ Failed to parse config.yaml: {e} → fallback to env")
        return _env_fallback()

    srv = raw.get("server", {})
    m   = raw.get("model", {})

    server_cfg = {
        "host":      os.environ.get("SERVER_HOST",  str(srv.get("host",      "0.0.0.0"))),
        "port":      int(os.environ.get("SERVER_PORT",  srv.get("port",      10400))),
        "api_host":  os.environ.get("API_HOST",     str(srv.get("api_host",  "0.0.0.0"))),
        "api_port":  int(os.environ.get("API_PORT",     srv.get("api_port",  8090))),
        "log_level": os.environ.get("LOG_LEVEL",    str(srv.get("log_level", "INFO"))).upper(),
        "mode":      os.environ.get("MODE",         str(srv.get("mode",      "wyoming"))).lower(),
    }

    use_int8     = _get_bool("USE_INT8", m.get("use_int8", False))
    suffix       = ".int8.onnx" if use_int8 else ".onnx"
    base         = "epoch-20-avg-10"
    hf_model_id  = os.environ.get("HF_MODEL_ID", m.get("hf_model_id", "hynt/Zipformer-30M-RNNT-6000h"))

    encoder_file = os.environ.get("ENCODER_FILE", m.get("encoder_file", f"encoder-{base}{suffix}"))
    decoder_file = os.environ.get("DECODER_FILE", m.get("decoder_file", f"decoder-{base}{suffix}"))
    joiner_file  = os.environ.get("JOINER_FILE",  m.get("joiner_file",  f"joiner-{base}{suffix}"))
    tokens_file  = os.environ.get("TOKENS_FILE",  m.get("tokens_file",  "config.json"))

    req_env        = _get_list("REQUIRED_FILES", [])
    req_yaml       = m.get("required_files", [])
    required_files = req_env or req_yaml or [encoder_file, decoder_file, joiner_file, tokens_file]

    model_cfg = ModelConfig(
        id               = os.environ.get("MODEL_ID",
                               m.get("id", "default-asr")),
        display_name     = os.environ.get("MODEL_DISPLAY_NAME",
                               m.get("display_name", "Vietnamese ASR")),
        description      = os.environ.get("MODEL_DESCRIPTION",
                               m.get("description", "")),
        attribution_name = os.environ.get("MODEL_ATTRIBUTION_NAME",
                               m.get("attribution_name", hf_model_id.split("/")[0])),
        attribution_url  = os.environ.get("MODEL_ATTRIBUTION_URL",
                               m.get("attribution_url",
                                     f"https://huggingface.co/{hf_model_id}")),
        languages        = _get_list("MODEL_LANGUAGES",
                               m.get("languages", ["vi"])),
        hf_model_id      = hf_model_id,
        hf_token         = os.environ.get("HF_TOKEN",
                               m.get("hf_token") or "") or None,
        model_dir        = Path(os.environ.get("MODEL_DIR",
                               m.get("model_dir", "/app/model"))),
        required_files   = required_files,
        encoder_file     = encoder_file,
        decoder_file     = decoder_file,
        joiner_file      = joiner_file,
        tokens_file      = tokens_file,
        use_int8         = use_int8,
        num_threads      = _get_int("NUM_THREADS",  m.get("num_threads",  4)),
        sample_rate      = _get_int("SAMPLE_RATE",  m.get("sample_rate",  16000)),
        provider         = os.environ.get("PROVIDER", m.get("provider", "cpu")),
        force_download   = _get_bool("FORCE_DOWNLOAD", m.get("force_download", False)),
    )
    return server_cfg, model_cfg


# ─────────────────────────────────────────────
# Download & Ensure
# ─────────────────────────────────────────────
def _missing_files(cfg: ModelConfig) -> List[str]:
    return [f for f in cfg.required_files if not (cfg.model_dir / f).exists()]


def download_model(cfg: ModelConfig):
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        _LOGGER.error("huggingface_hub not installed!")
        raise

    cfg.model_dir.mkdir(parents=True, exist_ok=True)
    _LOGGER.info(f"📥 Downloading: {cfg.hf_model_id} → {cfg.model_dir}")
    _LOGGER.info(f"   Required files: {cfg.required_files}")

    # allow_patterns = exact filenames + bpe.model (optional tokenizer)
    allow_patterns = list(cfg.required_files)
    if "bpe.model" not in allow_patterns:
        allow_patterns.append("bpe.model")

    snapshot_download(
        repo_id=cfg.hf_model_id,
        local_dir=str(cfg.model_dir),
        allow_patterns=allow_patterns,
        token=cfg.hf_token,
    )

    still_missing = _missing_files(cfg)
    if still_missing:
        raise RuntimeError(
            f"❌ Download incomplete! Still missing: {still_missing}\n"
            f"   Check HF repo '{cfg.hf_model_id}' for correct filenames."
        )
    _LOGGER.info(f"✅ Download complete: {[f.name for f in cfg.model_dir.iterdir()]}")


def ensure_model(cfg: ModelConfig):
    lock_file = cfg.model_dir / ".download.lock"
    cfg.model_dir.mkdir(parents=True, exist_ok=True)

    with open(lock_file, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            if cfg.force_download:
                _LOGGER.info("🔄 FORCE_DOWNLOAD=true → re-downloading")
                download_model(cfg)
                return
            missing = _missing_files(cfg)
            if missing:
                _LOGGER.warning(f"⚠️  Missing: {missing} → downloading")
                download_model(cfg)
            else:
                _LOGGER.info(f"✅ All files present: {cfg.required_files}")
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


# ─────────────────────────────────────────────
# Model Loader
# ─────────────────────────────────────────────
def load_model(cfg: ModelConfig):
    _LOGGER.info("=" * 55)
    _LOGGER.info(f"Loading model: [{cfg.id}] {cfg.display_name}")
    _LOGGER.info(f"  ENCODER  : {cfg.encoder_path}")
    _LOGGER.info(f"  DECODER  : {cfg.decoder_path}")
    _LOGGER.info(f"  JOINER   : {cfg.joiner_path}")
    _LOGGER.info(f"  TOKENS   : {cfg.tokens_path}")
    _LOGGER.info(f"  THREADS  : {cfg.num_threads} | PROVIDER: {cfg.provider}")
    _LOGGER.info(f"  USE_INT8 : {cfg.use_int8}")
    _LOGGER.info("=" * 55)

    for path, label in [
        (cfg.encoder_path, "ENCODER"),
        (cfg.decoder_path, "DECODER"),
        (cfg.joiner_path,  "JOINER"),
        (cfg.tokens_path,  "TOKENS"),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"❌ {label} not found: {path}")

    cfg.recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=str(cfg.encoder_path),
        decoder=str(cfg.decoder_path),
        joiner=str(cfg.joiner_path),
        tokens=str(cfg.tokens_path),
        num_threads=cfg.num_threads,
        sample_rate=cfg.sample_rate,
        provider=cfg.provider,
        decoding_method="greedy_search",
    )
    _LOGGER.info(f"✅ Model loaded: [{cfg.id}]")


# ─────────────────────────────────────────────
# Global state
# ─────────────────────────────────────────────
_MODEL_CFG: Optional[ModelConfig] = None
_SERVER_CFG: dict = {}

# ─────────────────────────────────────────────
# ══════════════════════════════════════════════
# MODE: WYOMING
# ══════════════════════════════════════════════
# ─────────────────────────────────────────────
def _run_wyoming():
    """Start Wyoming protocol server"""
    from wyoming.asr import Transcribe, Transcript
    from wyoming.audio import AudioChunk, AudioStart, AudioStop
    from wyoming.event import Event
    from wyoming.info import AsrModel, AsrProgram, Attribution, Describe, Info
    from wyoming.server import AsyncEventHandler, AsyncServer

    class ASREventHandler(AsyncEventHandler):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.audio_buffer = bytearray()
            self.sample_rate  = _MODEL_CFG.sample_rate
            self.channels     = 1

        def _transcribe(self) -> str:
            audio_data = (
                np.frombuffer(self.audio_buffer, dtype=np.int16)
                .astype(np.float32) / 32768.0
            )
            if self.channels > 1:
                audio_data = audio_data.reshape(-1, self.channels).mean(axis=1)
            stream = _MODEL_CFG.recognizer.create_stream()
            stream.accept_waveform(self.sample_rate, audio_data)
            _MODEL_CFG.recognizer.decode_stream(stream)
            return _normalize_text(stream.result.text)

        def _build_info(self) -> Info:
            cfg = _MODEL_CFG
            return Info(
                asr=[AsrProgram(
                    name=cfg.id,
                    attribution=Attribution(
                        name=cfg.attribution_name,
                        url=cfg.attribution_url,
                    ),
                    installed=True,
                    description=cfg.description,
                    models=[AsrModel(
                        name=cfg.id,
                        attribution=Attribution(
                            name=cfg.attribution_name,
                            url=cfg.attribution_url,
                        ),
                        installed=True,
                        description=cfg.description,
                        languages=cfg.languages,
                    )],
                )]
            )

        async def handle_event(self, event: Event) -> bool:

            if Describe.is_type(event.type):
                _LOGGER.info("Handling Describe event")
                await self.write_event(self._build_info().event())
                return True

            if AudioStart.is_type(event.type):
                audio_start       = AudioStart.from_event(event)
                self.sample_rate  = audio_start.rate
                self.channels     = audio_start.channels
                self.audio_buffer = bytearray()
                _LOGGER.info(f"Audio started: rate={self.sample_rate}, ch={self.channels}")
                return True

            if AudioChunk.is_type(event.type):
                chunk = AudioChunk.from_event(event)
                self.audio_buffer.extend(chunk.audio)
                _LOGGER.debug(f"Chunk: {len(chunk.audio)} bytes")
                return True

            if AudioStop.is_type(event.type):
                _LOGGER.info(f"Audio stopped, buffer: {len(self.audio_buffer)} bytes")
                if not self.audio_buffer:
                    _LOGGER.warning("Empty audio buffer")
                    await self.write_event(Transcript(text="").event())
                    return True
                try:
                    text = self._transcribe()
                    _LOGGER.info(f"[{_MODEL_CFG.id}] Transcription: '{text}'")
                    await self.write_event(Transcript(text=text).event())
                except Exception as e:
                    _LOGGER.error(f"Transcription error: {e}", exc_info=True)
                    await self.write_event(Transcript(text="").event())
                finally:
                    self.audio_buffer = bytearray()
                return True

            if Transcribe.is_type(event.type):
                _LOGGER.info("Transcribe event received")
                if self.audio_buffer:
                    try:
                        text = self._transcribe()
                        _LOGGER.info(f"[{_MODEL_CFG.id}] Transcription: '{text}'")
                        await self.write_event(Transcript(text=text).event())
                    except Exception as e:
                        _LOGGER.error(f"Transcription error: {e}", exc_info=True)
                        await self.write_event(Transcript(text="").event())
                    finally:
                        self.audio_buffer = bytearray()
                return True

            _LOGGER.debug(f"Unhandled event: {event.type}")
            return True

    async def _wyoming_main():
        host = _SERVER_CFG.get("host", "0.0.0.0")
        port = _SERVER_CFG.get("port", 10400)
        uri  = f"tcp://{host}:{port}"

        def handler_factory(reader, writer):
            return ASREventHandler(reader, writer)

        server = AsyncServer.from_uri(uri)
        _LOGGER.info(f"✅ Wyoming server listening on {uri}")
        await server.run(handler_factory)

    asyncio.run(_wyoming_main())


# ─────────────────────────────────────────────
# ══════════════════════════════════════════════
# MODE: FASTAPI
# ══════════════════════════════════════════════
# ─────────────────────────────────────────────
def _run_fastapi():
    """Start FastAPI REST server"""
    import uvicorn
    import soundfile as sf
    from fastapi import FastAPI, File, HTTPException, UploadFile
    from fastapi.responses import PlainTextResponse

    # ── Metrics ──────────────────────────────
    _metrics = {
        "requests_total":    0,
        "requests_success":  0,
        "requests_error":    0,
        "total_audio_seconds": 0.0,
        "total_inference_ms":  0.0,
    }

    # ── Lifespan ─────────────────────────────
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _LOGGER.info(f"✅ FastAPI ready on "
                     f"{_SERVER_CFG['api_host']}:{_SERVER_CFG['api_port']}")
        yield
        _LOGGER.info("🛑 FastAPI shutting down...")

    # ── App ───────────────────────────────────
    cfg = _MODEL_CFG
    app = FastAPI(
        title=cfg.display_name,
        version="1.0.0",
        description=cfg.description,
        lifespan=lifespan,
    )

    # ── /health ───────────────────────────────
    @app.get("/health")
    async def health():
        success = _metrics["requests_success"]
        return {
            "status": "healthy",
            "model_id": cfg.id,
            "model_name": cfg.display_name,
            "hf_model_id": cfg.hf_model_id,
            "variant": "int8" if cfg.use_int8 else "fp32",
            "languages": cfg.languages,
            "provider": cfg.provider,
            "num_threads": cfg.num_threads,
            "sample_rate": cfg.sample_rate,
            "metrics": {
                "requests_total":      _metrics["requests_total"],
                "requests_success":    success,
                "requests_error":      _metrics["requests_error"],
                "total_audio_seconds": round(_metrics["total_audio_seconds"], 2),
                "avg_inference_ms":    round(
                    _metrics["total_inference_ms"] / max(success, 1), 1
                ),
            },
        }

    # ── /metrics (Prometheus) ─────────────────
    @app.get("/metrics", response_class=PlainTextResponse)
    async def prometheus_metrics():
        success = _metrics["requests_success"]
        avg_ms  = _metrics["total_inference_ms"] / max(success, 1)
        return (
            f'# HELP asr_requests_total Total transcription requests\n'
            f'# TYPE asr_requests_total counter\n'
            f'asr_requests_total {_metrics["requests_total"]}\n\n'
            f'# HELP asr_requests_success Successful transcriptions\n'
            f'# TYPE asr_requests_success counter\n'
            f'asr_requests_success {success}\n\n'
            f'# HELP asr_requests_error Failed transcriptions\n'
            f'# TYPE asr_requests_error counter\n'
            f'asr_requests_error {_metrics["requests_error"]}\n\n'
            f'# HELP asr_audio_seconds_total Total audio duration processed\n'
            f'# TYPE asr_audio_seconds_total counter\n'
            f'asr_audio_seconds_total {_metrics["total_audio_seconds"]:.3f}\n\n'
            f'# HELP asr_inference_ms_avg Average inference latency ms\n'
            f'# TYPE asr_inference_ms_avg gauge\n'
            f'asr_inference_ms_avg {avg_ms:.1f}\n'
        )

    # ── /transcribe ───────────────────────────
    @app.post("/transcribe")
    async def transcribe(audio: UploadFile = File(...)):
        if cfg.recognizer is None:
            raise HTTPException(status_code=503, detail="Model not loaded")

        _metrics["requests_total"] += 1
        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                content  = await audio.read()
                tmp.write(content)
                tmp_path = tmp.name

            audio_data, sample_rate = sf.read(tmp_path)
            _LOGGER.info(
                f"Audio: {len(audio_data)} samples @ {sample_rate}Hz, "
                f"shape={audio_data.shape}"
            )

            # Mono
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)

            # Resample
            if sample_rate != cfg.sample_rate:
                from scipy.signal import resample_poly
                import math
                gcd        = math.gcd(cfg.sample_rate, sample_rate)
                audio_data = resample_poly(
                    audio_data,
                    up=cfg.sample_rate // gcd,
                    down=sample_rate   // gcd,
                )
                _LOGGER.info(f"Resampled: {sample_rate}Hz → {cfg.sample_rate}Hz")

            audio_data = audio_data.astype(np.float32)
            duration   = len(audio_data) / cfg.sample_rate

            # Inference
            t_start  = time.perf_counter()
            stream   = cfg.recognizer.create_stream()
            stream.accept_waveform(cfg.sample_rate, audio_data)
            cfg.recognizer.decode_stream(stream)
            infer_ms = (time.perf_counter() - t_start) * 1000

            text = _normalize_text(stream.result.text)
            rtf  = infer_ms / 1000 / max(duration, 0.001)

            _LOGGER.info(
                f"[{cfg.id}] '{text}' | "
                f"dur={duration:.2f}s | infer={infer_ms:.1f}ms | RTF={rtf:.3f}"
            )

            _metrics["requests_success"]    += 1
            _metrics["total_audio_seconds"] += duration
            _metrics["total_inference_ms"]  += infer_ms

            return {
                "text":         text,
                "duration":     round(duration, 3),
                "inference_ms": round(infer_ms, 1),
                "rtf":          round(rtf, 4),
            }

        except Exception as e:
            _metrics["requests_error"] += 1
            _LOGGER.error(f"Transcription error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)

    # ── Run uvicorn ───────────────────────────
    uvicorn.run(
        app,
        host=_SERVER_CFG["api_host"],
        port=_SERVER_CFG["api_port"],
        log_level=_SERVER_CFG["log_level"].lower(),
    )


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
def main():
    global _MODEL_CFG, _SERVER_CFG

    _LOGGER.info("🚀 Starting ASR Server")

    # Step 1: Load config
    _SERVER_CFG, model_cfg = load_config()

    # Re-apply log level
    logging.getLogger().setLevel(
        getattr(logging, _SERVER_CFG.get("log_level", "INFO"), logging.INFO)
    )

    mode = _SERVER_CFG.get("mode", "wyoming")
    _LOGGER.info(f"📋 MODE      : {mode.upper()}")
    _LOGGER.info(f"📋 Model     : [{model_cfg.id}] {model_cfg.display_name}")
    _LOGGER.info(f"📋 HF source : {model_cfg.hf_model_id}")
    _LOGGER.info(f"📋 Model dir : {model_cfg.model_dir}")
    _LOGGER.info(f"📋 Req files : {model_cfg.required_files}")

    # Step 2: Ensure + Load model
    ensure_model(model_cfg)
    load_model(model_cfg)
    _MODEL_CFG = model_cfg

        # Step 3: Branch theo MODE
    if mode == "fastapi":
        _LOGGER.info(
            f"🌐 Starting FastAPI on "
            f"{_SERVER_CFG['api_host']}:{_SERVER_CFG['api_port']}"
        )
        _run_fastapi()
    else:
        _LOGGER.info(
            f"📡 Starting Wyoming on "
            f"{_SERVER_CFG['host']}:{_SERVER_CFG['port']}"
        )
        _run_wyoming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        _LOGGER.info("Server stopped by user")
    except Exception as e:
        _LOGGER.error(f"Server error: {e}", exc_info=True)
        raise
