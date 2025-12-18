
import sys
from types import ModuleType
from unittest.mock import MagicMock
from datetime import datetime, timezone
from dataclasses import dataclass

# Helper to create a dummy module
def create_mock_module(name):
    m = ModuleType(name)
    sys.modules[name] = m
    return m

# Mock 'homeassistant'
ha = create_mock_module("homeassistant")

# Mock 'homeassistant.core'
ha_core = create_mock_module("homeassistant.core")
ha_core.callback = lambda x: x
ha_core.HomeAssistant = MagicMock()
class ServiceCall:
    pass
ha_core.ServiceCall = ServiceCall
class CoreState:
    NOT_RUNNING = "not_running"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
ha_core.CoreState = CoreState

# Mock 'homeassistant.exceptions'
ha_exceptions = create_mock_module("homeassistant.exceptions")
class HomeAssistantError(Exception):
    pass
ha_exceptions.HomeAssistantError = HomeAssistantError
ha_exceptions.ConfigEntryNotReady = HomeAssistantError

# Mock 'homeassistant.config_entries'
ha_config_entries = create_mock_module("homeassistant.config_entries")
class ConfigEntry:
    def __init__(self, version=1, minor_version=1, domain="test", title="test", data=None, options=None, unique_id=None):
        self.version = version
        self.minor_version = minor_version
        self.domain = domain
        self.title = title
        self.data = data or {}
        self.options = options or {}
        self.unique_id = unique_id
        self.entry_id = "test_entry_id"

ha_config_entries.ConfigEntry = ConfigEntry
ha_config_entries.ConfigFlow = MagicMock()
ha_config_entries.OptionsFlow = MagicMock()
ha_config_entries.ConfigError = Exception
ha_config_entries.ConfigFlowResult = dict

# Mock 'homeassistant.const'
ha_const = create_mock_module("homeassistant.const")
ha_const.CONF_REGION = "region"
ha_const.CONF_USERNAME = "username"
ha_const.CONF_PASSWORD = "password"
ha_const.CONF_URL = "url"
ha_const.CONF_LLM_HASS_API = "llm_hass_api" # Sometimes used
ha_const.EVENT_HOMEASSISTANT_STARTED = "homeassistant_started"
ha_const.PERCENTAGE = "%"
ha_const.EntityCategory = MagicMock()
ha_const.EntityCategory.CONFIG = "config"
ha_const.EntityCategory.DIAGNOSTIC = "diagnostic"

ha_const.UnitOfLength = MagicMock()
ha_const.UnitOfLength.KILOMETERS = "km"
ha_const.UnitOfLength.MILES = "mi"
ha_const.UnitOfTemperature = MagicMock()
ha_const.UnitOfTemperature.CELSIUS = "celsius"
ha_const.UnitOfTemperature.FAHRENHEIT = "fahrenheit"
ha_const.UnitOfPressure = MagicMock()
ha_const.UnitOfPressure.PSI = "psi"
ha_const.UnitOfPressure.BAR = "bar"
ha_const.UnitOfPressure.KPA = "kpa"
ha_const.UnitOfSpeed = MagicMock()
ha_const.UnitOfSpeed.KILOMETERS_PER_HOUR = "km/h"
ha_const.UnitOfSpeed.MILES_PER_HOUR = "mph"
ha_const.UnitOfElectricCurrent = MagicMock()
ha_const.UnitOfElectricCurrent.AMPERE = "A"
ha_const.UnitOfPower = MagicMock()
ha_const.UnitOfPower.WATT = "W"
ha_const.UnitOfPower.KILO_WATT = "kW"
ha_const.UnitOfTemperature = MagicMock()
ha_const.UnitOfTemperature.CELSIUS = "celsius"
ha_const.UnitOfPressure = MagicMock()
ha_const.UnitOfPressure.PSI = "psi"
ha_const.UnitOfPressure.BAR = "bar"
ha_const.UnitOfPressure.KPA = "kpa"
ha_const.UnitOfTime = MagicMock()
ha_const.UnitOfTime.SECONDS = "seconds"
ha_const.UnitOfTime.MINUTES = "minutes"
ha_const.UnitOfTime.HOURS = "hours"
ha_const.UnitOfTime.DAYS = "days"
ha_const.CONF_NAME = "name"
class Platform:
    SENSOR = "sensor"
ha_const.Platform = Platform
ha_const.STATE_UNKNOWN = "unknown"
ha_const.STATE_UNAVAILABLE = "unavailable"
ha_const.CONF_DEVICE_TRACKER = "device_tracker"

# Mock 'homeassistant.util'
ha_util = create_mock_module("homeassistant.util")

# Mock 'homeassistant.util.dt'
ha_util_dt = create_mock_module("homeassistant.util.dt")
def as_local(d):
    return d
def parse_datetime(d):
    if d == "1970-01-01T00:00:00.000Z":
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(d.replace("Z", "+00:00"))
    except:
        return datetime.now(timezone.utc)
    
ha_util_dt.as_local = as_local
ha_util_dt.parse_datetime = parse_datetime
ha_util_dt.utcnow = lambda: datetime.now(timezone.utc)
ha_util_dt.now = lambda: datetime.now(timezone.utc)
ha_util.dt = ha_util_dt

# Mock 'homeassistant.util.unit_system'
ha_util_us = create_mock_module("homeassistant.util.unit_system")
class UnitSystem:
    def __init__(self):
        self.pressure_unit = "psi"
    def length(self, value, unit):
        return value 
    def temperature(self, value, unit):
        return value
    def pressure(self, value, unit):
        return value

ha_util_us.UnitSystem = UnitSystem
ha_util_us.METRIC_SYSTEM = UnitSystem()

# Mock 'homeassistant.helpers'
ha_helpers = create_mock_module("homeassistant.helpers")

# Mock 'homeassistant.helpers.aiohttp_client'
ha_helpers_aiohttp = create_mock_module("homeassistant.helpers.aiohttp_client")
ha_helpers_aiohttp.async_get_clientsession = MagicMock()
ha_helpers_aiohttp.async_create_clientsession = MagicMock()

# Mock 'homeassistant.helpers.event'
ha_helpers_event = create_mock_module("homeassistant.helpers.event")
ha_helpers_event.async_track_time_interval = MagicMock()
ha_helpers_event.async_track_state_change_event = MagicMock()

# Mock 'homeassistant.helpers.entity'
ha_helpers_entity = create_mock_module("homeassistant.helpers.entity")
class Entity:
    pass
class DeviceInfo:
    def __init__(self, **kwargs):
        pass
@dataclass(frozen=True)
class EntityDescription:
    key: str
    name: str | None = None
    icon: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    native_unit_of_measurement: str | None = None
    entity_category: str | None = None
    entity_registry_enabled_default: bool = True
    suggested_display_precision: int | None = None
    has_entity_name: bool = False
    suggested_unit_of_measurement: str | None = None
    translation_key: str | None = None
    options: list[str] | None = None
    entity_registry_visible_default: bool = True
    
ha_helpers_entity.Entity = Entity
ha_helpers_entity.DeviceInfo = DeviceInfo
ha_helpers_entity.EntityDescription = EntityDescription

ha_helpers_entity.EntityDescription = EntityDescription

# Mock 'homeassistant.helpers.storage'
ha_helpers_storage = create_mock_module("homeassistant.helpers.storage")
ha_helpers_storage.STORAGE_DIR = ".storage"

# Mock 'homeassistant.helpers.device_registry'
ha_helpers_dr = create_mock_module("homeassistant.helpers.device_registry")
class DeviceRegistry:
    pass
ha_helpers_dr.DeviceRegistry = DeviceRegistry
ha_helpers_dr.async_get = MagicMock()

# Mock 'homeassistant.helpers.entity_registry'
ha_helpers_er = create_mock_module("homeassistant.helpers.entity_registry")
ha_helpers_er.async_get = MagicMock()

# Mock 'homeassistant.helpers.entity_registry'
ha_helpers_er = create_mock_module("homeassistant.helpers.entity_registry")
ha_helpers_er.async_get = MagicMock()

# Mock 'homeassistant.helpers.typing'
ha_helpers_typing = create_mock_module("homeassistant.helpers.typing")
class UndefinedType:
    pass
ha_helpers_typing.UndefinedType = UndefinedType
ha_helpers_typing.UNDEFINED = UndefinedType()

# Mock 'homeassistant.helpers.update_coordinator'
ha_helpers_uc = create_mock_module("homeassistant.helpers.update_coordinator")
class DataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval=None, update_method=None):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.data = {}
        self.update_method = update_method
    
    async def async_refresh(self):
        if self.update_method:
            self.data = await self.update_method()
            
class CoordinatorEntity(Entity):
    def __init__(self, coordinator):
        self.coordinator = coordinator

ha_helpers_uc.DataUpdateCoordinator = DataUpdateCoordinator
ha_helpers_uc.CoordinatorEntity = CoordinatorEntity
ha_helpers_uc.UpdateFailed = Exception

ha_helpers_uc.CoordinatorEntity = CoordinatorEntity
ha_helpers_uc.UpdateFailed = Exception

# Mock 'homeassistant.loader'
ha_loader = create_mock_module("homeassistant.loader")
ha_loader.async_get_integration = MagicMock()

# Mock 'homeassistant.components'
ha_components = create_mock_module("homeassistant.components")

# Mock 'homeassistant.components'
ha_components = create_mock_module("homeassistant.components")

# Mock 'homeassistant.components.button'
ha_components_button = create_mock_module("homeassistant.components.button")
@dataclass(frozen=True)
class ButtonEntityDescription(EntityDescription):
    pass
ha_components_button.ButtonEntityDescription = ButtonEntityDescription

# Mock 'homeassistant.components.sensor'
ha_components_sensor = create_mock_module("homeassistant.components.sensor")
class SensorEntity(Entity):
        pass
ha_components_sensor.SensorEntity = SensorEntity
@dataclass(frozen=True)
class SensorEntityDescription(EntityDescription):
    pass
class SensorStateClass:
    MEASUREMENT = "measurement"
    TOTAL = "total"
    TOTAL_INCREASING = "total_increasing"
class SensorDeviceClass:
    BATTERY = "battery"
    CURRENT = "current"
    ENERGY = "energy"
    FREQUENCY = "frequency"
    GAS = "gas"
    HUMIDITY = "humidity"
    ILLUMINANCE = "illuminance"
    MONETARY = "monetary"
    NITROGEN_DIOXIDE = "nitrogen_dioxide"
    NITROGEN_MONOXIDE = "nitrogen_monoxide"
    NITROUS_OXIDE = "nitrous_oxide"
    OZONE = "ozone"
    PM1 = "pm1"
    PM10 = "pm10"
    PM25 = "pm25"
    POWER_FACTOR = "power_factor"
    POWER = "power"
    PRESSURE = "pressure"
    SIGNAL_STRENGTH = "signal_strength"
    SULPHUR_DIOXIDE = "sulphur_dioxide"
    TEMPERATURE = "temperature"
    TIMESTAMP = "timestamp"
    VOLATILE_ORGANIC_COMPOUNDS = "volatile_organic_compounds"
    VOLTAGE = "voltage"
    DISTANCE = "distance"
    SPEED = "speed"
    VOLUME = "volume"
    WEIGHT = "weight"
    DURATION = "duration"
    # Add generic fallback if needed, but these cover most
ha_components_sensor.SensorEntityDescription = SensorEntityDescription
ha_components_sensor.SensorStateClass = SensorStateClass
ha_components_sensor.SensorDeviceClass = SensorDeviceClass

# Mock 'homeassistant.components.switch'
ha_components_switch = create_mock_module("homeassistant.components.switch")
@dataclass(frozen=True)
class SwitchEntityDescription(EntityDescription):
    pass
ha_components_switch.SwitchEntityDescription = SwitchEntityDescription

# Mock 'homeassistant.components.lock'
ha_components_lock = create_mock_module("homeassistant.components.lock")
@dataclass(frozen=True)
class LockEntityDescription(EntityDescription):
    pass
ha_components_lock.LockEntityDescription = LockEntityDescription

# Mock 'homeassistant.components.binary_sensor'
ha_components_binary_sensor = create_mock_module("homeassistant.components.binary_sensor")
class BinarySensorEntityDescription:
    pass
ha_components_binary_sensor.BinarySensorEntityDescription = BinarySensorEntityDescription

# Mock 'homeassistant.components.binary_sensor'
ha_components_binary_sensor = create_mock_module("homeassistant.components.binary_sensor")
@dataclass(frozen=True)
class BinarySensorEntityDescription(EntityDescription):
    pass
ha_components_binary_sensor.BinarySensorEntityDescription = BinarySensorEntityDescription

# Mock 'homeassistant.components.number'
ha_components_number = create_mock_module("homeassistant.components.number")
@dataclass(frozen=True)
class NumberEntityDescription(EntityDescription):
    native_min_value: float | None = None
    native_max_value: float | None = None
    native_step: float | None = None
    mode: str | None = None
class NumberMode:
    AUTO = "auto"
    BOX = "box"
    SLIDER = "slider"
class NumberDeviceClass:
    APPARENT_POWER = "apparent_power"
    AQI = "aqi"
    ATMOSPHERIC_PRESSURE = "atmospheric_pressure"
    BATTERY = "battery"
    CO2 = "carbon_dioxide"
    CO = "carbon_monoxide"
    CURRENT = "current"
    DATA_RATE = "data_rate"
    DATA_SIZE = "data_size"
    DATE = "date"
    DISTANCE = "distance"
    DURATION = "duration"
    ENERGY = "energy"
    ENERGY_STORAGE = "energy_storage"
    FREQUENCY = "frequency"
    GAS = "gas"
    HUMIDITY = "humidity"
    ILLUMINANCE = "illuminance"
    IRRADIANCE = "irradiance"
    MOISTURE = "moisture"
    MONETARY = "monetary"
    NITROGEN_DIOXIDE = "nitrogen_dioxide"
    NITROGEN_MONOXIDE = "nitrogen_monoxide"
    NITROUS_OXIDE = "nitrous_oxide"
    OZONE = "ozone"
    PH = "ph"
    PM1 = "pm1"
    PM10 = "pm10"
    PM25 = "pm25"
    POWER_FACTOR = "power_factor"
    POWER = "power"
    PRECIPITATION = "precipitation"
    PRECIPITATION_INTENSITY = "precipitation_intensity"
    PRESSURE = "pressure"
    REACTIVE_POWER = "reactive_power"
    SIGNAL_STRENGTH = "signal_strength"
    SOUND_PRESSURE = "sound_pressure"
    SPEED = "speed"
    SULPHUR_DIOXIDE = "sulphur_dioxide"
    TEMPERATURE = "temperature"
    TIMESTAMP = "timestamp"
    VOLATILE_ORGANIC_COMPOUNDS = "volatile_organic_compounds"
    VOLTAGE = "voltage"
    VOLUME = "volume"
    WATER = "water"
    WEIGHT = "weight"
    WIND_SPEED = "wind_speed"
ha_components_number.NumberEntityDescription = NumberEntityDescription
ha_components_number.NumberMode = NumberMode
ha_components_number.NumberDeviceClass = NumberDeviceClass

ha_components_number.NumberDeviceClass = NumberDeviceClass

# Mock 'homeassistant.components.text'
ha_components_text = create_mock_module("homeassistant.components.text")
@dataclass(frozen=True)
class TextEntityDescription(EntityDescription):
    pass
ha_components_text.TextEntityDescription = TextEntityDescription

# Mock 'homeassistant.components.select'
ha_components_select = create_mock_module("homeassistant.components.select")
@dataclass(frozen=True)
class SelectEntityDescription(EntityDescription):
    options: list[str] | None = None
ha_components_select.SelectEntityDescription = SelectEntityDescription

# Mock 'homeassistant.components.update'
ha_components_update = create_mock_module("homeassistant.components.update")
@dataclass(frozen=True)
class UpdateEntityDescription(EntityDescription):
    pass
ha_components_update.UpdateEntityDescription = UpdateEntityDescription

# Mock 'homeassistant.components.device_tracker'
ha_components_dt = create_mock_module("homeassistant.components.device_tracker")
class SourceType:
    GPS = "gps"
ha_components_dt.SourceType = SourceType

# Mock 'homeassistant.components.device_tracker.config_entry'
ha_components_dt_ce = create_mock_module("homeassistant.components.device_tracker.config_entry")
class TrackerEntity:
    pass
ha_components_dt_ce.TrackerEntity = TrackerEntity

# Mock Entity Platform
ha_helpers_entity_platform = create_mock_module("homeassistant.helpers.entity_platform")
ha_helpers_entity_platform.AddEntitiesCallback = MagicMock()

# Ensure 'custom_components' can be imported
# typically this works if the directory is there, but we might need to add current dir to path
import os
sys.path.append(os.getcwd())
