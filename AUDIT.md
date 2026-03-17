# Wyoming Vietnamese ASR - Code Audit Report

## 📋 Structure Created

```
wyoming-hacs/
├── .github/workflows/release.yml    # GitHub Actions for release + Docker build
├── custom_components/wyoming_vietnamese/
│   ├── __init__.py                  # HA integration entry point
│   ├── config_flow.py               # UI configuration flow
│   ├── const.py                     # Constants
│   ├── manifest.json                # HACS manifest
│   ├── services.yaml                # Service definitions
│   ├── strings.json                 # Localization
│   └── stt.py                       # STT provider (Wyoming client)
├── docker/
│   ├── compose.yaml                 # Standalone Docker deployment
│   ├── Dockerfile                   # Wyoming server image
│   ├── Dockerfile.fastapi           # FastAPI server image
│   ├── server/main.py               # Original Wyoming server (copied)
│   └── fastapi_server.py            # Original FastAPI server (copied)
├── hacs.json                        # HACS metadata
├── README.md                        # Documentation
├── requirements.txt                 # Python dependencies
├── LICENSE                          # MIT License
└── .gitignore                       # Git ignore rules
```

## ✅ HACS Compliance Check

| Requirement | Status | Notes |
|-------------|--------|-------|
| **manifest.json** | ✅ Present | Domain: `wyoming_vietnamese`, version: 1.0.0 |
| **hacs.json** | ✅ Present | Integration type, HA version 2024.1.0+ |
| **config_flow.py** | ✅ Present | UI configuration with validation |
| **strings.json** | ✅ Present | Vietnamese/English localization |
| **README.md** | ✅ Present | Installation, usage, troubleshooting |
| **LICENSE** | ✅ MIT | Permissive open source |
| **GitHub Release** | ✅ Automated | Actions create ZIP on tag push |
| **Docker Support** | ✅ Maintained | Standalone docker-compose for external use |

## 🔍 Code Audit - Original Server Files

### **server/main.py (Wyoming Protocol)**

**Strengths:**
- ✅ Proper async/await pattern with `AsyncServer` and `AsyncEventHandler`
- ✅ Comprehensive logging for debugging
- ✅ Wyoming protocol compliance (`Describe`, `AudioStart`, `AudioChunk`, `AudioStop`, `Transcribe`)
- ✅ Multi-channel to mono conversion
- ✅ Graceful error handling with empty transcript on failure

**Issues Found:**
1. **Duplicate Transcribe handling** (lines 117-144 and 145-168):
   - `Transcribe` event and `AudioStop` event both handle transcription
   - **Risk:** Logic duplication, harder to maintain
   - **Fix:** Extract transcription logic to a helper method

2. **No graceful shutdown:**
   - `KeyboardInterrupt` is caught but no cleanup of resources
   - **Fix:** Add signal handlers for SIGTERM/SIGINT

3. **Hardcoded model paths:**
   - `/app/model` is hardcoded
   - **Fix:** Use environment variable `MODEL_PATH`

4. **No audio validation:**
   - No check for sample rate compatibility (assumes 16kHz)
   - **Fix:** Add sample rate validation and resampling

### **fastapi_server.py (REST API)**

**Strengths:**
- ✅ FastAPI with proper OpenAPI documentation
- ✅ Health endpoint for monitoring
- ✅ File upload handling
- ✅ Temporary file cleanup

**Issues Found:**
1. **Missing scipy import for resampling:**
   ```python
   if sample_rate != 16000:
       import scipy.signal  # Imported inside condition
   ```
   **Risk:** Import inside conditional may fail silently
   **Fix:** Import at top of file, add to requirements.txt

2. **No file size validation:**
   - Large audio files could cause memory issues
   - **Fix:** Add max file size check

3. **Temporary file security:**
   - Uses `tempfile.NamedTemporaryFile(delete=False)`
   - **Risk:** File not deleted on crash
   - **Fix:** Use context manager with cleanup in `finally`

4. **No rate limiting:**
   - API has no rate limiting
   - **Fix:** Add rate limiting for production use

## 🛠️ Improvements Made in HACS Version

### **config_flow.py**
- ✅ Added connection test during configuration
- ✅ Proper error handling for connection failures
- ✅ Options flow for runtime configuration changes

### **stt.py (HA STT Provider)**
- ✅ Async audio stream processing
- ✅ Proper timeout handling (30 seconds)
- ✅ Connection error differentiation (timeout, refused, etc.)
- ✅ Language support declaration

### **GitHub Actions**
- ✅ Multi-architecture Docker builds (amd64, arm64)
- ✅ Automated release creation with ZIP
- ✅ Docker Hub push with version tags

## 📝 Recommendations

### **For Docker Deployment:**
1. Add health checks to both services
2. Use Docker secrets for sensitive data
3. Add resource limits (memory: 2G minimum)
4. Enable GPU passthrough for NVIDIA

### **For Home Assistant Integration:**
1. Test with HA 2024.1.0+ compatibility
2. Add entity customization options
3. Implement diagnostic sensors (connection status, model load status)
4. Add service for transcription via HA service call

### **For HACS Submission:**
1. Ensure all files are in repository
2. Create proper GitHub release with version tags
3. Test HACS installation locally
4. Submit to HACS default integration list

## 🚀 Next Steps

1. **Push to GitHub:**
   ```bash
   cd /root/.openclaw/workspace/wyoming-hacs
   git init
   git remote add origin git@github.com:gnolnos/wyoming-vietnamese-asr.git
   git add .
   git commit -m "HACS-ready structure"
   git push -u origin main
   ```

2. **Tag Release:**
   ```bash
   git tag v1.0.0
   git push --tags
   # GitHub Actions will create release + Docker images
   ```

3. **Test HACS Installation:**
   - Add custom repository to HACS
   - Install and configure in Home Assistant
   - Test STT functionality

4. **Submit to HACS:**
   - Fork hacs/default repository
   - Add integration to list
   - Submit pull request

## 🔧 Code Fixes Needed (Original Server)

### **server/main.py**
```python
# Add environment variable support
import os
MODEL_DIR = Path(os.getenv("MODEL_PATH", "/app/model"))

# Add graceful shutdown
import signal
async def shutdown(sig, loop):
    _LOGGER.info("Shutting down...")
    # Cleanup resources
    loop.stop()

# Extract transcription logic
async def transcribe_audio(self, audio_data, sample_rate, channels):
    # Shared logic for AudioStop and Transcribe events
```

### **fastapi_server.py**
```python
# Import scipy at top
import scipy.signal

# Add file size validation
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
if len(content) > MAX_FILE_SIZE:
    raise HTTPException(status_code=413, detail="File too large")

# Use context manager for temp files
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
    try:
        # Process file
    finally:
        Path(tmp.name).unlink(missing_ok=True)
```

## ✅ HACS Readiness Score: 85/100

**Missing 15 points:**
- 5: No test files
- 5: No CI/CD for testing
- 5: Original server code needs minor fixes

**Overall:** Ready for HACS submission after pushing to GitHub and creating first release.
