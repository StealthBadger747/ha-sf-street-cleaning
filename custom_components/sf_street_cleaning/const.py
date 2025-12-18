"""Constants for the SF Street Cleaning integration."""

DOMAIN = "sf_street_cleaning"

# GitHub URL for the neighborhood GeoJSON data
GEOJSON_URL = "https://raw.githubusercontent.com/kaushalpartani/sf-street-cleaning/refs/heads/main/data/neighborhoods/Marina.geojson"

# Configuration Keys
CONF_DEVICE_TRACKER = "device_tracker_id"

# Events
EVENT_ALERT = "sf_street_cleaning_alert"

# Attributes
ATTR_STREET = "street"
ATTR_SIDE = "side"
ATTR_NEXT_CLEANING = "next_cleaning"
ATTR_NEXT_CLEANING_START = "next_cleaning_start"
ATTR_NEXT_CLEANING_END = "next_cleaning_end"
ATTR_CLEANING_IN_HOURS = "cleaning_in_hours"
ATTR_DISTANCE = "distance_to_segment"
