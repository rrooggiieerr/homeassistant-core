"""Support for ADS sensors."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.sensor import (
    CONF_STATE_CLASS,
    DEVICE_CLASSES_SCHEMA as SENSOR_DEVICE_CLASSES_SCHEMA,
    PLATFORM_SCHEMA as SENSOR_PLATFORM_SCHEMA,
    STATE_CLASSES_SCHEMA as SENSOR_STATE_CLASSES_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME, CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, StateType

from .. import ads
from . import ADS_TYPEMAP, CONF_ADS_FACTOR, CONF_ADS_TYPE
from .const import CONF_ADS_VAR, DATA_ADS, STATE_KEY_STATE
from .entity import AdsEntity

DEFAULT_NAME = "ADS sensor"

PLATFORM_SCHEMA = SENSOR_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADS_VAR): cv.string,
        vol.Optional(CONF_ADS_FACTOR): cv.positive_int,
        vol.Optional(CONF_ADS_TYPE, default=ads.ADSTYPE_INT): vol.In(
            [
                ads.ADSTYPE_BOOL,
                ads.ADSTYPE_BYTE,
                ads.ADSTYPE_INT,
                ads.ADSTYPE_UINT,
                ads.ADSTYPE_SINT,
                ads.ADSTYPE_USINT,
                ads.ADSTYPE_DINT,
                ads.ADSTYPE_UDINT,
                ads.ADSTYPE_WORD,
                ads.ADSTYPE_DWORD,
                ads.ADSTYPE_LREAL,
                ads.ADSTYPE_REAL,
            ]
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_DEVICE_CLASS): SENSOR_DEVICE_CLASSES_SCHEMA,
        vol.Optional(CONF_STATE_CLASS): SENSOR_STATE_CLASSES_SCHEMA,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up an ADS sensor device."""
    ads_hub = hass.data[DATA_ADS]

    ads_var: str = config[CONF_ADS_VAR]
    ads_type: str = config[CONF_ADS_TYPE]
    name: str = config[CONF_NAME]
    factor: int | None = config.get(CONF_ADS_FACTOR)
    device_class: SensorDeviceClass | None = config.get(CONF_DEVICE_CLASS)
    state_class: SensorStateClass | None = config.get(CONF_STATE_CLASS)
    unit_of_measurement: str | None = config.get(CONF_UNIT_OF_MEASUREMENT)

    entity = AdsSensor(
        ads_hub,
        ads_var,
        ads_type,
        name,
        factor,
        device_class,
        state_class,
        unit_of_measurement,
    )

    add_entities([entity])


class AdsSensor(AdsEntity, SensorEntity):
    """Representation of an ADS sensor entity."""

    def __init__(
        self,
        ads_hub: ads.AdsHub,
        ads_var: str,
        ads_type: str,
        name: str,
        factor: int | None,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        unit_of_measurement: str | None,
    ) -> None:
        """Initialize AdsSensor entity."""
        super().__init__(ads_hub, name, ads_var)
        self._ads_type = ads_type
        self._factor = factor
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit_of_measurement

    async def async_added_to_hass(self) -> None:
        """Register device notification."""
        await self.async_initialize_device(
            self._ads_var,
            ADS_TYPEMAP[self._ads_type],
            STATE_KEY_STATE,
            self._factor,
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the device."""
        return self._state_dict[STATE_KEY_STATE]
