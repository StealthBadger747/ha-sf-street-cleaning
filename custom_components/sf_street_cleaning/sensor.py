"""Sensor platform for SF Street Cleaning."""
from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_DEVICE_TRACKER,
    ATTR_STREET,
    ATTR_SIDE,
    ATTR_NEXT_CLEANING,
    ATTR_NEXT_CLEANING_START,
    ATTR_NEXT_CLEANING_END,
    ATTR_CLEANING_IN_HOURS,
    ATTR_DISTANCE,
)
from .geometry import find_cleaning_data

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    device_tracker_id = entry.data.get(CONF_DEVICE_TRACKER)
    geojson = hass.data[DOMAIN].get("geojson")
    
    if not device_tracker_id:
        _LOGGER.error("No device_tracker_id found in config entry")
        return

    async_add_entities([SFStreetCleaningSensor(hass, device_tracker_id, geojson)], True)


class SFStreetCleaningSensor(SensorEntity):
    """Reflects the street cleaning status of the parked vehicle."""

    _attr_name = "SF Street Cleaning Status"
    _attr_icon = "mdi:broom"
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, device_tracker_id: str, geojson: dict):
        """Initialize the sensor."""
        self.hass = hass
        self._device_tracker_id = device_tracker_id
        self._geojson = geojson
        self._state = STATE_UNKNOWN
        self._attributes = {}
        self._attr_unique_id = f"sf_street_cleaning_{device_tracker_id}"
        
        # Track last alert to avoid spamming
        self._last_alert_time: dict[str, datetime] = {}

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        # Listen for state changes of the tracker
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._device_tracker_id], self._async_on_tracker_update
            )
        )
        self._update_sensor_state()

    @callback
    def _async_on_tracker_update(self, event) -> None:
        """Called when the device tracker state changes."""
        self._update_sensor_state()
        self.async_write_ha_state()

    def _update_sensor_state(self) -> None:
        """Retrieve new data and update the sensor state."""
        tracker_state = self.hass.states.get(self._device_tracker_id)
        if not tracker_state or tracker_state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            self._state = STATE_UNKNOWN
            return

        try:
            lat = float(tracker_state.attributes.get("latitude", 0))
            lon = float(tracker_state.attributes.get("longitude", 0))
            # Try different potential attribute names for heading
            img_rot = tracker_state.attributes.get("course", tracker_state.attributes.get("heading", tracker_state.attributes.get("compassDirection")))
            
            rotation = 0
            if img_rot is not None:
                try:
                    rotation = int(float(img_rot)) % 360
                except ValueError:
                    pass
            
            # Use geometry logic
            result = find_cleaning_data(self._geojson, lat, lon, rotation)
            
            if not result:
                self._state = "Unknown Location"
                self._attributes = {}
                return

            self._attributes = {
                ATTR_STREET: result.get("street"),
                ATTR_SIDE: result.get("parkedOnSide"),
                ATTR_DISTANCE: result.get("distance"),
                "median": result.get("median")
            }
            
            next_cleaning_raw = result.get("nextCleaning")
            
            # Parsing cleaning time
            # Expected format: {'NextCleaning': '2025-12-18T09:00:00-08:00', ...} or just a string?
            # Based on user's code, it seems to be a dict with key 'NextCleaning' or a string.
            
            cleaning_dt = None
            if isinstance(next_cleaning_raw, dict):
                cleaning_str = next_cleaning_raw.get("NextCleaning")
                self._attributes[ATTR_NEXT_CLEANING] = cleaning_str
                if cleaning_str and cleaning_str != "Unknown":
                    try:
                        cleaning_dt = datetime.fromisoformat(cleaning_str)
                    except ValueError:
                        pass
            elif isinstance(next_cleaning_raw, str):
                 self._attributes[ATTR_NEXT_CLEANING] = next_cleaning_raw
                 if next_cleaning_raw != "Unknown":
                     try:
                        cleaning_dt = datetime.fromisoformat(next_cleaning_raw)
                     except ValueError:
                        pass
            
            if cleaning_dt:
                now = dt_util.now()
                delta = cleaning_dt - now
                hours_until = delta.total_seconds() / 3600.0
                self._attributes[ATTR_CLEANING_IN_HOURS] = round(hours_until, 1)
                self._attributes[ATTR_NEXT_CLEANING_START] = cleaning_dt.isoformat()
                
                # Determine State
                if hours_until < 0:
                     # Currently sweeping? Or just passed? We assume 2h duration if unknown
                     if hours_until > -2.0:
                         self._state = "Sweeping Now"
                     else:
                         self._state = "Clear" # Passed
                elif hours_until < 24:
                    self._state = "Warning"
                else:
                    self._state = "Clear"
                    
            else:
                self._state = "No Schedule Found"
                self._attributes[ATTR_CLEANING_IN_HOURS] = -1

        except Exception as e:
            _LOGGER.error("Error updating street cleaning sensor: %s", e)
            self._state = "Error"
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes
