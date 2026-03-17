"""Speech-to-Text platform for Wyoming Vietnamese ASR."""
import asyncio
import logging
from typing import AsyncGenerator, Optional

from homeassistant.components.stt import (
    STTProvider,
    SpeechMetadata,
    SpeechResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    DEFAULT_HOST,
    DEFAULT_PORT,
)

_LOGGER = logging.getLogger(__name__)


async def async_get_engine(hass: HomeAssistant, config: ConfigType, entry: Optional[ConfigEntry] = None):
    """Set up STT provider."""
    if entry is None:
        return None
    
    host = entry.data.get(CONF_HOST, DEFAULT_HOST)
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    
    return WyomingVietnameseSTT(hass, host, port)


class WyomingVietnameseSTT(STTProvider):
    """Wyoming Vietnamese ASR STT provider."""

    def __init__(self, hass: HomeAssistant, host: str, port: int):
        """Initialize STT provider."""
        self.hass = hass
        self.host = host
        self.port = port
        self._language = "vi"
        self._name = "Vietnamese ASR"

    @property
    def default_language(self) -> str:
        """Return default language."""
        return self._language

    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return ["vi"]

    @property
    def name(self) -> str:
        """Return the name of the provider."""
        return self._name

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncGenerator[bytes, None]
    ) -> SpeechResult:
        """Process audio stream and return transcription."""
        try:
            # Collect audio data
            audio_data = b""
            async for chunk in stream:
                audio_data += chunk
            
            if not audio_data:
                return SpeechResult(
                    text="",
                    success=False,
                    error="No audio data received"
                )

            # Connect to Wyoming server
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=30
            )
            
            # Send audio data
            writer.write(audio_data)
            await writer.drain()
            
            # Read response (simplified protocol)
            response = await asyncio.wait_for(
                reader.read(65536),
                timeout=30
            )
            
            writer.close()
            await writer.wait_closed()
            
            # Parse response (simplified - actual protocol may differ)
            text = response.decode("utf-8", errors="ignore").strip()
            
            if text:
                return SpeechResult(
                    text=text,
                    success=True
                )
            else:
                return SpeechResult(
                    text="",
                    success=False,
                    error="Empty response from server"
                )
                
        except asyncio.TimeoutError:
            return SpeechResult(
                text="",
                success=False,
                error="Connection timeout"
            )
        except ConnectionRefusedError:
            return SpeechResult(
                text="",
                success=False,
                error="Connection refused"
            )
        except Exception as err:
            _LOGGER.error("Speech processing error: %s", err)
            return SpeechResult(
                text="",
                success=False,
                error=f"Processing error: {err}"
            )
