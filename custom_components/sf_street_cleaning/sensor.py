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
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_DEVICE_TRACKER,
    GEOJSON_URL,
    GEOJSON_REFRESH_INTERVAL_HOURS,
    NEIGHBORHOODS_INDEX_URL,
    NEIGHBORHOOD_FILE_URL_TEMPLATE,
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
    geojson_url = hass.data[DOMAIN].get("geojson_url", GEOJSON_URL)
    neighborhoods_index = hass.data[DOMAIN].get("neighborhoods_index")
    
    if not device_tracker_id:
        _LOGGER.error("No device_tracker_id found in config entry")
        return

    async_add_entities([SFStreetCleaningSensor(hass, device_tracker_id, geojson, geojson_url, neighborhoods_index)], True)


class SFStreetCleaningSensor(SensorEntity):
    """Reflects the street cleaning status of the parked vehicle."""

    _attr_name = "SF Street Cleaning Status"
    _attr_icon = "mdi:broom"
    _attr_has_entity_name = True
    _attr_should_poll = True  # allow HA to poll in case tracker events are missed

    def __init__(self, hass: HomeAssistant, device_tracker_id: str, geojson: dict, geojson_url: str | None, neighborhoods_index: dict | None):
        """Initialize the sensor."""
        self.hass = hass
        self._device_tracker_id = device_tracker_id
        self._geojson = geojson
        self._geojson_url = geojson_url  # None triggers neighborhood auto-detect
        self._neighborhoods_index = neighborhoods_index
        self._state = STATE_UNKNOWN
        self._attributes = {}
        self._attr_unique_id = f"sf_street_cleaning_{device_tracker_id}"
        
        # Track last alert to avoid spamming
        self._last_alert_time: dict[str, datetime] = {}
        # Cache neighborhood geojsons to avoid refetching
        self._neighborhood_geojsons: dict[str, dict] = {}

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        # Listen for state changes of the tracker
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._device_tracker_id], self._async_on_tracker_update
            )
        )
        self._update_sensor_state()

    async def async_update(self) -> None:
        """Poll fallback: refresh from latest tracker state."""
        await self._async_ensure_geojson()
        self._update_sensor_state()

    async def _async_ensure_geojson(self) -> None:
        """Refresh GeoJSON daily in case upstream data changes."""
        data = self.hass.data.setdefault(DOMAIN, {})

        # If user supplied an explicit URL, honor it
        if self._geojson_url:
            await self._async_fetch_geojson(self._geojson_url, data)
            return

        # Otherwise: auto-select neighborhood based on point-in-polygon
        if not self._neighborhoods_index:
            self._neighborhoods_index = await self._async_fetch_neighborhood_index(data)
        if not self._neighborhoods_index:
            return

        tracker_state = self.hass.states.get(self._device_tracker_id)
        if not tracker_state:
            return
        try:
            lat = float(tracker_state.attributes.get("latitude", 0))
            lon = float(tracker_state.attributes.get("longitude", 0))
        except Exception:
            return

        neighborhood_file = self._find_neighborhood_file(lat, lon, self._neighborhoods_index)
        if not neighborhood_file:
            return

        neighborhood_url = NEIGHBORHOOD_FILE_URL_TEMPLATE.format(file=neighborhood_file)
        await self._async_fetch_geojson(neighborhood_url, data)

    async def _async_fetch_neighborhood_index(self, data: dict) -> dict | None:
        """Fetch neighborhoods index (MultiPolygon per neighborhood)."""
        try:
            session = async_get_clientsession(self.hass)
            _LOGGER.info("Street cleaning: fetching neighborhoods index from %s", NEIGHBORHOODS_INDEX_URL)
            async with session.get(NEIGHBORHOODS_INDEX_URL) as resp:
                resp.raise_for_status()
                index = await resp.json(content_type=None)
                data["neighborhoods_index"] = index
                return index
        except Exception as err:
            _LOGGER.warning("Street cleaning: failed to fetch neighborhoods index (%s)", err)
            return None

    async def _async_fetch_geojson(self, url: str, data: dict) -> None:
        """Fetch a GeoJSON street segment file with caching and refresh interval."""
        data = self.hass.data.setdefault(DOMAIN, {})
        geojson = data.get("geojson")
        fetched_at = data.get("geojson_fetched_at")
        now = dt_util.utcnow()
        stale = (
            geojson is None
            or fetched_at is None
            or (now - fetched_at) > timedelta(hours=GEOJSON_REFRESH_INTERVAL_HOURS)
        )
        if not stale:
            self._geojson = geojson
            return
        try:
            session = async_get_clientsession(self.hass)
            _LOGGER.info("Street cleaning: refreshing GeoJSON from %s", url)
            async with session.get(url) as resp:
                resp.raise_for_status()
                # GitHub raw returns text/plain; allow parse despite content-type
                new_geojson = await resp.json(content_type=None)
                data["geojson"] = new_geojson
                data["geojson_fetched_at"] = now
                self._geojson = new_geojson
                _LOGGER.debug("Street cleaning: refreshed GeoJSON with %d features", len(new_geojson.get("features", [])))
        except Exception as err:
            _LOGGER.warning("Street cleaning: failed to refresh GeoJSON (%s)", err)
            # Keep existing cached geojson if available
            if geojson:
                self._geojson = geojson

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
            _LOGGER.debug("Street cleaning: tracker %s unavailable or missing", self._device_tracker_id)
            return

        try:
            lat = float(tracker_state.attributes.get("latitude", 0))
            lon = float(tracker_state.attributes.get("longitude", 0))
            _LOGGER.debug("Street cleaning: tracker %s lat=%s lon=%s", self._device_tracker_id, lat, lon)
            # Try different potential attribute names for heading
            img_rot = tracker_state.attributes.get("course", tracker_state.attributes.get("heading", tracker_state.attributes.get("compassDirection")))
            if img_rot is None:
                # Fallback: check FordPass GPS sensor for heading/compassDirection
                gps_entity_id = (
                    self._device_tracker_id
                    .replace("device_tracker.", "sensor.")
                    .replace("_tracker", "_gps")
                )
                gps_state = self.hass.states.get(gps_entity_id)
                if gps_state:
                    img_rot = gps_state.attributes.get(
                        "course",
                        gps_state.attributes.get(
                            "heading",
                            gps_state.attributes.get("compassDirection"),
                        ),
                    )
                    _LOGGER.debug("Street cleaning: heading fallback from %s -> %s", gps_entity_id, img_rot)
                else:
                    _LOGGER.debug("Street cleaning: heading fallback sensor %s not found", gps_entity_id)
            
            rotation = 0
            img_val = img_rot

            # Normalize heading type
            if isinstance(img_val, dict):
                img_val = (
                    img_val.get("heading")
                    or img_val.get("value")
                    or next(
                        (v for v in img_val.values() if isinstance(v, (int, float, str))),
                        None,
                    )
                )

            if isinstance(img_val, str):
                direction_map = {
                    "N": 0,
                    "NORTH": 0,
                    "NE": 45,
                    "NORTHEAST": 45,
                    "E": 90,
                    "EAST": 90,
                    "SE": 135,
                    "SOUTHEAST": 135,
                    "S": 180,
                    "SOUTH": 180,
                    "SW": 225,
                    "SOUTHWEST": 225,
                    "W": 270,
                    "WEST": 270,
                    "NW": 315,
                    "NORTHWEST": 315,
                }
                upper = img_val.strip().upper()
                if upper in direction_map:
                    img_val = direction_map[upper]

            try:
                if img_val is not None:
                    rotation = int(float(img_val)) % 360
            except (ValueError, TypeError):
                rotation = 0
            _LOGGER.debug("Street cleaning: heading=%s rotation=%s", img_val, rotation)
            
            # Use geometry logic
            result = find_cleaning_data(self._geojson, lat, lon, rotation)
            
            if not result:
                self._state = "Out of Coverage"
                self._attributes = {
                    "latitude": lat,
                    "longitude": lon,
                    "reason": "no_segment_match"
                }
                _LOGGER.debug("Street cleaning: no matching segment found for lat=%s lon=%s", lat, lon)
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
                _LOGGER.debug("Street cleaning: matched %s side=%s hours_until=%.2f", result.get('street'), result.get('parkedOnSide'), hours_until)
                    
            else:
                self._state = "No Schedule Found"
                self._attributes[ATTR_CLEANING_IN_HOURS] = -1
                _LOGGER.debug("Street cleaning: matched %s but no schedule found", result.get('street'))

        except Exception as e:
            _LOGGER.error("Error updating street cleaning sensor: %s", e)
            self._state = "Error"

    def _find_neighborhood_file(self, lat: float, lon: float, index: dict) -> str | None:
        """Return neighborhood file name if point is inside any polygon."""
        try:
            for feat in index.get("features", []):
                props = feat.get("properties", {})
                fname = props.get("FileName")
                geom = feat.get("geometry", {})
                if not fname or geom.get("type") != "MultiPolygon":
                    continue
                if self._point_in_multipolygon(lat, lon, geom.get("coordinates", [])):
                    return fname
        except Exception as err:
            _LOGGER.debug("Street cleaning: neighborhood detection failed: %s", err)
        return None

    def _point_in_polygon(self, lat: float, lon: float, ring: list[list[float]]) -> bool:
        """Ray casting for single polygon ring; ring is list of [lon, lat]."""
        inside = False
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i][0], ring[i][1]
            x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
            if ((y1 > lat) != (y2 > lat)) and (lon < (x2 - x1) * (lat - y1) / (y2 - y1 + 1e-12) + x1):
                inside = not inside
        return inside

    def _point_in_multipolygon(self, lat: float, lon: float, multipoly: list) -> bool:
        """Check point in multipolygon (list of polygons; each polygon is list of rings)."""
        for poly in multipoly:
            if not poly:
                continue
            exterior = poly[0]
            if self._point_in_polygon(lat, lon, exterior):
                return True
        return False
    
    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes
