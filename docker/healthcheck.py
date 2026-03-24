#!/usr/bin/env python3
"""
Healthcheck script - dùng trong Dockerfile HEALTHCHECK CMD
Hỗ trợ cả Wyoming (TCP) và FastAPI (HTTP /health)
"""
import os
import socket
import sys
import urllib.request
import urllib.error

MODE     = os.environ.get("MODE", "wyoming").lower()
API_HOST = os.environ.get("API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("API_PORT", 8090))
WY_HOST  = os.environ.get("SERVER_HOST", "0.0.0.0")
WY_PORT  = int(os.environ.get("SERVER_PORT", 10400))

# Wyoming bind 0.0.0.0 → check qua localhost
WY_CHECK_HOST = "127.0.0.1"

def check_wyoming() -> bool:
    """TCP connect check cho Wyoming protocol"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        result = s.connect_ex((WY_CHECK_HOST, WY_PORT))
        s.close()
        if result == 0:
            print(f"[OK] Wyoming TCP {WY_CHECK_HOST}:{WY_PORT} reachable")
            return True
        print(f"[FAIL] Wyoming TCP {WY_CHECK_HOST}:{WY_PORT} → errno={result}")
        return False
    except Exception as e:
        print(f"[FAIL] Wyoming check error: {e}")
        return False


def check_fastapi() -> bool:
    """HTTP GET /health check cho FastAPI"""
    url = f"http://{API_HOST}:{API_PORT}/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = resp.read().decode()
            if resp.status == 200:
                print(f"[OK] FastAPI {url} → {resp.status} {body[:80]}")
                return True
            print(f"[FAIL] FastAPI {url} → HTTP {resp.status}")
            return False
    except urllib.error.HTTPError as e:
        print(f"[FAIL] FastAPI HTTP error: {e.code} {e.reason}")
        return False
    except Exception as e:
        print(f"[FAIL] FastAPI check error: {e}")
        return False


if __name__ == "__main__":
    if MODE == "fastapi":
        ok = check_fastapi()
    else:
        ok = check_wyoming()

    sys.exit(0 if ok else 1)