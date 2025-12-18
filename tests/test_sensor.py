import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Import the local mock FIRST before any potential HA imports
import tests.mock_homeassistant as mock_ha

# Set up module paths to allow imports
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

# Force reload of the component modules to use the mock
for name in [
    "custom_components.sf_street_cleaning",
    "custom_components.sf_street_cleaning.sensor",
    "custom_components.sf_street_cleaning.const",
    "custom_components.sf_street_cleaning.geometry",
]:
    sys.modules.pop(name, None)

import custom_components.sf_street_cleaning.sensor as sensor_mod

class FakeState:
    def __init__(self, state, attributes):
        self.state = state
        self.attributes = attributes

class FakeStates:
    def __init__(self, mapping):
        self._map = mapping

    def get(self, entity_id):
        return self._map.get(entity_id)

class SensorTests(unittest.TestCase):
    def setUp(self):
        self.sensor_mod = sensor_mod

    def _make_sensor(self, tracker_attrs, geojson=None):
        tracker = FakeState("not_home", tracker_attrs)
        mapping = {tracker_attrs["entity_id"]: tracker}
        
        # Create a Mock HomeAssistant instance
        hass = MagicMock()
        hass.states = FakeStates(mapping)
        hass.data = {self.sensor_mod.DOMAIN: {}}
        
        sensor = self.sensor_mod.SFStreetCleaningSensor(
            hass=hass,
            device_tracker_id=tracker_attrs["entity_id"],
            geojson=geojson or {},
            geojson_url=None,
            neighborhoods_index=None,
        )
        return sensor

    def test_heading_fallback_logic(self):
        """Test looking for course, then heading, relative to the tracker entity attributes."""
        rotations = []

        def fake_find_cleaning_data(_geojson, _lat, _lon, rotation):
            rotations.append(rotation)
            return {
                "street": "Test",
                "parkedOnSide": f"rot-{rotation}",
                "distance": 1,
                "median": False,
                "nextCleaning": "2026-01-01T10:00:00-08:00",
            }

        self.sensor_mod.find_cleaning_data = fake_find_cleaning_data
        
        # Test 1: 'course' attribute
        tracker_attrs_course = {"entity_id": "device_tracker.test_truck", "latitude": 1.0, "longitude": 2.0, "course": 90}
        sensor = self._make_sensor(tracker_attrs_course)
        sensor._update_sensor_state()
        self.assertEqual(rotations[-1], 90, "Should use 'course' attribute")
        
        # Test 2: 'heading' attribute
        tracker_attrs_heading = {"entity_id": "device_tracker.test_truck", "latitude": 1.0, "longitude": 2.0, "heading": 180}
        sensor = self._make_sensor(tracker_attrs_heading)
        sensor._update_sensor_state()
        self.assertEqual(rotations[-1], 180, "Should fallback to 'heading' attribute")

        # Test 3: 'compassDirection' attribute conversion
        tracker_attrs_cardinal = {"entity_id": "device_tracker.test_truck", "latitude": 1.0, "longitude": 2.0, "compassDirection": "SOUTHWEST"}
        sensor = self._make_sensor(tracker_attrs_cardinal)
        sensor._update_sensor_state()
        self.assertEqual(rotations[-1], 225, "Should convert 'SOUTHWEST' to 225")

    def test_neighborhood_match(self):
        sensor = self._make_sensor({"entity_id": "device_tracker.test_truck", "latitude": 0.5, "longitude": 0.5})
        index = {
            "features": [
                {
                    "properties": {"FileName": "Square"},
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [0, 0],
                                    [1, 0],
                                    [1, 1],
                                    [0, 1],
                                    [0, 0],
                                ]
                            ]
                        ],
                    },
                }
            ]
        }
        fname = sensor._find_neighborhood_file(0.5, 0.5, index)
        self.assertEqual(fname, "Square")
        fname_none = sensor._find_neighborhood_file(2.0, 2.0, index)
        self.assertIsNone(fname_none)

if __name__ == "__main__":
    unittest.main()
