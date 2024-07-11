"""Watts Vision sensor platform -- central unit."""
from typing import Optional
from .const import DOMAIN
from .watts_api import WattsApi
from homeassistant.components.sensor import SensorEntity


class WattsVisionLastCommunicationSensor(SensorEntity):
    def __init__(self, wattsClient: WattsApi, smartHome: str, label: str, mac_address: str):
        super().__init__()
        self.client = wattsClient
        self.smartHome = smartHome
        self._label = label
        self._name = "Last communication " + self._label
        self._state = None
        self._available = True
        self._mac_address = mac_address

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return "last_communication_" + self.smartHome

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.smartHome)
            },
            "manufacturer": "Watts",
            "name": "Central Unit " + self._label,
            "model": "BT-CT02-RF",
            "connections": {
                ("mac", self._mac_address)
            }
        }

    async def async_update(self):
        data = await self.hass.async_add_executor_job(self.client.getLastCommunication, self.smartHome)

        self._state = "{} days, {} hours, {} minutes and {} seconds.".format(
            data["diffObj"]["days"],
            data["diffObj"]["hours"],
            data["diffObj"]["minutes"],
            data["diffObj"]["seconds"]
        )

class WattsVisionGlobalStatus(SensorEntity):
    def __init__(self, wattsClient: WattsApi, smartHome: str, label: str, mac_address: str):
        super().__init__()
        self.client = wattsClient
        self.smartHome = smartHome
        self._label = label
        self._name = "Global Status " + self._label
        self._state = "Off"
        self._available = True
        self._mac_address = mac_address

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return "global_status_" + self.smartHome

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.smartHome)
            },
            "manufacturer": "Watts",
            "name": "Central Unit " + self._label,
            "model": "BT-CT02-RF",
            "connections": {
                ("mac", self._mac_address)
            }
        }

    async def async_update(self):
        self._state = "Off"
        smartHome = self.client.getSmartHome(self.smartHome)
        for z in range(len(smartHome["zones"])):
            for x in range(len(smartHome["zones"][z]["devices"])):
                smartHomeDevice = smartHome["zones"][z]["devices"][x]
                if smartHomeDevice["heating_up"] != "0":
                    if smartHomeDevice["heat_cool"] == "1":
                        self._state = "Cooling"
                    else:
                        self._state = "Heating"

class WattsVisionGlobalDemand(SensorEntity):
    def __init__(self, wattsClient: WattsApi, smartHome: str, label: str, mac_address: str):
        super().__init__()
        self.client = wattsClient
        self.smartHome = smartHome
        self._label = label
        self._name = "Global Demand " + self._label
        self._state = 0
        self._available = True
        self._mac_address = mac_address

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return "global_demand_" + self.smartHome

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def state(self) -> int:
        return self._state

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.smartHome)
            },
            "manufacturer": "Watts",
            "name": "Central Unit " + self._label,
            "model": "BT-CT02-RF",
            "connections": {
                ("mac", self._mac_address)
            }
        }

    async def async_update(self):
        self._state = 0
        smartHome = self.client.getSmartHome(self.smartHome)
        for z in range(len(smartHome["zones"])):
            for x in range(len(smartHome["zones"][z]["devices"])):
                smartHomeDevice = smartHome["zones"][z]["devices"][x]
                if smartHomeDevice["heating_up"] != "0":
                    self._state = self._state + 1
        _LOGGER.debug("Demanding rooms: {}".format(self._state))
