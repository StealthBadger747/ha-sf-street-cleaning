"""The SF Street Cleaning integration."""
from __future__ import annotations

import logging
import json
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, GEOJSON_URL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the SF Street Cleaning integration component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SF Street Cleaning from a config entry."""
    
    hass.data.setdefault(DOMAIN, {})
    geojson_url = entry.data.get("geojson_url")
    hass.data[DOMAIN]["geojson_url"] = geojson_url
    
    # Load GeoJSON Data
    # We load this once during setup and store it in hass.data
    if "geojson" not in hass.data[DOMAIN]:
        try:
            session = async_get_clientsession(hass)
            _LOGGER.info("Fetching SF Street Cleaning GeoJSON from %s", geojson_url)
            async with session.get(geojson_url) as response:
                response.raise_for_status()
                # GitHub raw returns text/plain; allow parse despite content-type
                geojson_data = await response.json(content_type=None)
                hass.data[DOMAIN]["geojson"] = geojson_data
                _LOGGER.info("Successfully loaded %d features from GeoJSON", len(geojson_data.get("features", [])))
        except Exception as err:
            _LOGGER.error("Error fetching/parsing GeoJSON data: %s", err)
            # We can still proceed, but the sensor will be useless until reload
            hass.data[DOMAIN]["geojson"] = {}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
