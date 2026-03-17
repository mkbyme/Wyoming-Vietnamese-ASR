"""Wyoming Vietnamese ASR integration for Home Assistant."""
import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_NAME,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_NAME,
    SERVICE_TRANSCRIBE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["stt", "tts"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wyoming Vietnamese ASR from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        CONF_HOST: entry.data.get(CONF_HOST, DEFAULT_HOST),
        CONF_PORT: entry.data.get(CONF_PORT, DEFAULT_PORT),
        CONF_NAME: entry.data.get(CONF_NAME, DEFAULT_NAME),
    }

    # Register service
    async def handle_transcribe(call: ServiceCall) -> None:
        """Handle the transcribe service call."""
        audio_data = call.data.get("audio")
        if not audio_data:
            _LOGGER.error("No audio data provided")
            return

        # Forward to Wyoming server
        host = entry.data.get(CONF_HOST, DEFAULT_HOST)
        port = entry.data.get(CONF_PORT, DEFAULT_PORT)
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=30
            )
            writer.write(audio_data)
            await writer.drain()
            response = await reader.read()
            writer.close()
            await writer.wait_closed()
            
            # Process response (simplified)
            _LOGGER.info("Transcription received: %s", response.decode())
        except Exception as err:
            _LOGGER.error("Transcription failed: %s", err)

    hass.services.async_register(DOMAIN, SERVICE_TRANSCRIBE, handle_transcribe)

    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.services.async_remove(DOMAIN, SERVICE_TRANSCRIBE)

    return unload_ok


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Wyoming Vietnamese ASR component."""
    hass.data.setdefault(DOMAIN, {})
    return True
