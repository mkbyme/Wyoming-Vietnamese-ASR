# Wyoming Vietnamese ASR Add-on
FROM ghcr.io/gnolnos/wyoming-vietnamese-asr:latest

# Labels for Home Assistant
LABEL \
    io.hass.name="Wyoming Vietnamese ASR" \
    io.hass.description="Vietnamese Automatic Speech Recognition using Wyoming protocol." \
    io.hass.arch="amd64|aarch64" \
    io.hass.type="addon" \
    io.hass.version="1.0.0" \
    org.opencontainers.image.title="Wyoming Vietnamese ASR" \
    org.opencontainers.image.description="Vietnamese ASR for Home Assistant" \
    org.opencontainers.image.vendor="gnolnos" \
    org.opencontainers.image.authors="gnolnos <https://github.com/gnolnos>" \
    org.opencontainers.image.url="https://github.com/gnolnos/Wyoming-Vietnamese-ASR" \
    org.opencontainers.image.source="https://github.com/gnolnos/Wyoming-Vietnamese-ASR"

USER root

WORKDIR /app

EXPOSE 10400 8090

CMD ["python3", "server/main.py"]
