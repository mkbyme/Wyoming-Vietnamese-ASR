## 🧪 Kiểm thử

### Chế độ FastAPI (HTTP :8090)

```bash
# 1. Kiểm tra trạng thái
curl http://localhost:8090/health

# 2. Chuyển đổi audio (multipart/form-data — ĐÚNG)
curl -X POST "http://localhost:8090/transcribe" \
  -F "audio=@audio.wav"

# 3. Kết quả đẹp hơn
curl -X POST "http://localhost:8090/transcribe" \
  -F "audio=@audio.wav" | python -m json.tool

# 4. Prometheus metrics
curl http://localhost:8090/metrics
```

**Kết quả mong đợi:**
```json
{
  "text": "xin chào",
  "duration": 2.048,
  "inference_ms": 312.5,
  "rtf": 0.1526
}
```

&gt; ⚠️ **Content-Type**: FastAPI dùng `multipart/form-data` (`-F`), **không phải** `--data-binary` hay `-H "Content-Type: audio/wav"`.

---

### Chế độ Wyoming (TCP :10400)

Wyoming dùng giao thức nhị phân qua TCP — không test được bằng `curl`. Dùng một trong các cách sau:

#### Cách A: `wyoming-cli` (chính thức)

```bash
pip install wyoming

# Describe — lấy thông tin model server đang expose
wyoming-cli --uri tcp://localhost:10400 describe

# Transcribe file audio
wyoming-cli --uri tcp://localhost:10400 transcribe --audio-file audio.wav
```

#### Cách B: Kiểm tra kết nối TCP nhanh

```bash
nc -zv localhost 10400

# Hoặc
timeout 3 bash -c 'cat &lt; /dev/null &gt; /dev/tcp/localhost/10400' \
  &amp;&amp; echo "✅ Cổng 10400 MỞ" \
  || echo "❌ Cổng 10400 ĐÓNG"
```

#### Cách C: Python client

```python
#!/usr/bin/env python3
"""Test Wyoming ASR — Dùng: python test_wyoming.py [audio.wav] [host] [port]"""
import asyncio, sys
import numpy as np
import soundfile as sf
from pathlib import Path
from wyoming.asr import Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncTcpClient
from wyoming.info import Describe

HOST = sys.argv[2] if len(sys.argv) &gt; 2 else "localhost"
PORT = int(sys.argv[3]) if len(sys.argv) &gt; 3 else 10400
AUDIO_FILE = sys.argv[1] if len(sys.argv) &gt; 1 else "audio.wav"

async def main():
    async with AsyncTcpClient(HOST, PORT) as client:
        await client.write_event(Describe().event())
        ev = await client.read_event()
        print(f"[Describe] {ev.type}: {ev.data}")

    if Path(AUDIO_FILE).exists():
        audio, sr = sf.read(AUDIO_FILE)
        if audio.ndim &gt; 1: audio = audio.mean(axis=1)
        pcm = (audio.astype(np.float32) * 32768).clip(-32768, 32767).astype(np.int16)

        async with AsyncTcpClient(HOST, PORT) as client:
            await client.write_event(AudioStart(rate=sr, width=2, channels=1).event())
            await client.write_event(AudioChunk(audio=pcm.tobytes(), rate=sr, width=2, channels=1).event())
            await client.write_event(AudioStop().event())
            ev = await client.read_event()
            if Transcript.is_type(ev.type):
                print(f"[Transcript] '{Transcript.from_event(ev).text}'")

asyncio.run(main())
```

```bash
pip install wyoming soundfile numpy
python test_wyoming.py audio.wav
python test_wyoming.py audio.wav 192.168.100.150 10400
```

#### Chuẩn bị file audio test

```bash
# Chuyển đổi sang 16kHz mono WAV
ffmpeg -i input.mp3 -ar 16000 -ac 1 audio.wav

# Tạo file silence 2s để test kết nối
python -c "
import numpy as np, soundfile as sf
sf.write('test_silence.wav', np.zeros(32000, dtype=np.float32), 16000)
"
```

---

### Bảng so sánh cách test

| Cách | Dùng khi | Cần cài thêm |
|---|---|---|
| `curl -F` | Test FastAPI HTTP | có sẵn |
| `wyoming-cli describe` | Xác minh thông tin model | `pip install wyoming` |
| `wyoming-cli transcribe` | Test end-to-end Wyoming | `pip install wyoming` |
| `nc -zv` | Kiểm tra TCP port nhanh | có sẵn |
| `test_wyoming.py` | Debug chi tiết / CI | `wyoming soundfile numpy` |
| `healthcheck.py` | Xác minh health container | có sẵn trong image |
