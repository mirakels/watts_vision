"""Watts Vision sensor platform."""
from datetime import timedelta
import logging
from typing import Callable, Optional

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.helpers.typing import HomeAssistantType
from numpy import NaN

from .const import API_CLIENT, DOMAIN, PRESET_MODE_MAP, CONSIGNE_MAP
from .watts_api import WattsApi
from .central_unit import WattsVisionLastCommunicationSensor, WattsVisionGlobalStatus, WattsVisionGlobalDemand

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType,
    config_entry: ConfigEntry,
    async_add_entities: Callable
):
    """Set up the sensor platform."""

    wattsClient: WattsApi = hass.data[DOMAIN][API_CLIENT]

    smartHomes = wattsClient.getSmartHomes()

    sensors = []

    if smartHomes is not None:
        for y in range(len(smartHomes)):
            if smartHomes[y]["zones"] is not None:
                for z in range(len(smartHomes[y]["zones"])):
                    if smartHomes[y]["zones"][z]["devices"] is not None:
                        for x in range(len(smartHomes[y]["zones"][z]["devices"])):
                            sensors.append(
                                WattsVisionThermostatSensor(
                                    wattsClient,
                                    smartHomes[y]["smarthome_id"],
                                    smartHomes[y]["zones"][z]["devices"][x]["id"],
                                    smartHomes[y]["zones"][z]["zone_label"]
                                )
                            )
                            sensors.append(
                                WattsVisionTemperatureSensor(
                                    wattsClient,
                                    smartHomes[y]["smarthome_id"],
                                    smartHomes[y]["zones"][z]["devices"][x]["id"],
                                    smartHomes[y]["zones"][z]["zone_label"]
                                )
                            )
                            sensors.append(
                                WattsVisionSetTemperatureSensor(
                                    wattsClient,
                                    smartHomes[y]["smarthome_id"],
                                    smartHomes[y]["zones"][z]["devices"][x]["id"],
                                    smartHomes[y]["zones"][z]["zone_label"]
                                )
                            )
                            sensors.append(
                                WattsVisionBatterySensor(
                                    wattsClient,
                                    smartHomes[y]["smarthome_id"],
                                    smartHomes[y]["zones"][z]["devices"][x]["id"],
                                    smartHomes[y]["zones"][z]["zone_label"]
                                )
                            )
            sensors.append(
                WattsVisionLastCommunicationSensor(
                    wattsClient,
                    smartHomes[y]["smarthome_id"],
                    smartHomes[y]["label"],
                    smartHomes[y]["mac_address"]
                )
            )
            sensors.append(
                WattsVisionGlobalStatus(
                    wattsClient,
                    smartHomes[y]["smarthome_id"],
                    smartHomes[y]["label"],
                    smartHomes[y]["mac_address"]
                )
            )
            sensors.append(
                WattsVisionGlobalDemand(
                    wattsClient,
                    smartHomes[y]["smarthome_id"],
                    smartHomes[y]["label"],
                    smartHomes[y]["mac_address"]
                )
            )

    async_add_entities(sensors, update_before_add=True)


class WattsVisionThermostatSensor(SensorEntity):
    """Representation of a Watts Vision thermostat."""

    def __init__(self, wattsClient: WattsApi, smartHome: str, id: str, zone: str):
        super().__init__()
        self.client = wattsClient
        self.smartHome = smartHome
        self.id = id
        self.zone = zone
        self._name = "Heating mode " + zone
        self._state = None
        self._available = True

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return "thermostat_mode_" + self.id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def device_class(self):
        return SensorDeviceClass.ENUM

    @property
    def options(self):
        return list(PRESET_MODE_MAP.values())

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.id)
            },
            "manufacturer": "Watts",
            "name": "Thermostat " + self.zone,
            "model": "BT-D03-RF",
            "via_device": (DOMAIN, self.smartHome),
            "suggested_area": self.zone
        }

    async def async_update(self):
        # try:
        smartHomeDevice = self.client.getDevice(self.smartHome, self.id)

        self._state = PRESET_MODE_MAP[smartHomeDevice["gv_mode"]]

        # except:
        #     self._available = False
        #     _LOGGER.exception("Error retrieving data.")


class WattsVisionBatterySensor(SensorEntity):
    """Representation of the state of a Watts Vision device."""
    def __init__(self, wattsClient: WattsApi, smartHome: str, id: str, zone: str):
        super().__init__()
        self.client = wattsClient
        self.smartHome = smartHome
        self.id = id
        self.zone = zone
        self._name = "Battery " + zone
        self._state = None
        self._available = None

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return "battery_" + self.id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def device_class(self):
        return SensorDeviceClass.BATTERY

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

    @property
    def state(self) -> int:
        rc = 100
        err = self.client.getDevice(self.smartHome, self.id)['error_code']:
        if err & 0x0001:
            _LOGGER.warning('Battery needs attention for device %s ', self.name)
            rc = 5
        if err & 0x0800:
            _LOGGER.warning('No RF communication for device %s ', self.name)
            rc = 0
        if err & 0xF7FE:
            _LOGGER.warning('Other error for device %s: %s ', self.name, err)
            rc = 0
        return rc

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.id)
            },
            "manufacturer": "Watts",
            "name": "Thermostat " + self.zone,
            "model": "BT-D03-RF",
            "via_device": (DOMAIN, self.smartHome)
        }

class WattsVisionTemperatureSensor(SensorEntity):
    """Representation of a Watts Vision temperature sensor."""

    def __init__(self, wattsClient: WattsApi, smartHome: str, id: str, zone: str):
        super().__init__()
        self.client = wattsClient
        self.smartHome = smartHome
        self.id = id
        self.zone = zone
        self._name = "Air temperature " + zone
        self._state = None
        self._available = True

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return "temperature_air_" + self.id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self):
        return UnitOfTemperature.FAHRENHEIT

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.id)
            },
            "manufacturer": "Watts",
            "name": "Thermostat " + self.zone,
            "model": "BT-D03-RF",
            "via_device": (DOMAIN, self.smartHome)
        }

    async def async_update(self):
        # try:
        smartHomeDevice = self.client.getDevice(self.smartHome, self.id)
        value = int(smartHomeDevice["temperature_air"])
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            self._state = int((value - 320) * 5 / 9) / 10
        else:
            self._state = value / 10
        # except:
        #     self._available = False
        #     _LOGGER.exception("Error retrieving data.")


class WattsVisionSetTemperatureSensor(SensorEntity):
    """Representation of a Watts Vision temperature sensor."""

    def __init__(self, wattsClient: WattsApi, smartHome: str, id: str, zone: str):
        super().__init__()
        self.client = wattsClient
        self.smartHome = smartHome
        self.id = id
        self.zone = zone
        self._name = "Target temperature " + zone
        self._state = None
        self._available = True

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return "target_temperature_" + self.id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self):
        return UnitOfTemperature.FAHRENHEIT

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.id)
            },
            "manufacturer": "Watts",
            "name": "Thermostat " + self.zone,
            "model": "BT-D03-RF",
            "via_device": (DOMAIN, self.smartHome)
        }

    async def async_update(self):
        # try:
        smartHomeDevice = self.client.getDevice(self.smartHome, self.id)

        if smartHomeDevice["gv_mode"] == "1":
            self._state = NaN
        else:
            value = int(smartHomeDevice[CONSIGNE_MAP[smartHomeDevice["gv_mode"]]])
            if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
                self._state = int((value - 320) * 5 / 9) / 10
            else:
                self._state = value / 10

        # except:
        #     self._available = False
        #     _LOGGER.exception("Error retrieving data.")
