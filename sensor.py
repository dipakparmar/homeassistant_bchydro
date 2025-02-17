"""Sensor platform for the BC Hydro integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import ENERGY_KILO_WATT_HOUR, CURRENCY_DOLLAR, ATTR_DATE
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import BCHydroCoordinator


SENSOR_TYPES = {
    "latest_usage": {
        "name": "Latest Usage",
        "unit_of_measurement": ENERGY_KILO_WATT_HOUR,
        "icon": "mdi:flash",
    },
    "latest_cost": {
        "name": "Latest Cost",
        "unit_of_measurement": CURRENCY_DOLLAR,
        "icon": "mdi:currency-usd",
    },
    "billing_period_end": {
        "name": "Billing Period End",
        "unit_of_measurement": ATTR_DATE,
        "icon": "mdi:calendar",
    },
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up BC Hydro sensors based on a config entry."""
    coordinator: BCHydroCoordinator = hass.data["bchydro"][entry.entry_id]

    sensors = [
        BCHydroSensor(coordinator, sensor_type)
        for sensor_type in SENSOR_TYPES
    ]
    async_add_entities(sensors)


class BCHydroSensor(CoordinatorEntity, SensorEntity):
    """Representation of a BC Hydro sensor."""

    def __init__(self, coordinator: BCHydroCoordinator, sensor_type: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = SENSOR_TYPES[sensor_type]["name"]
        self._attr_unit_of_measurement = SENSOR_TYPES[sensor_type]["unit_of_measurement"]
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._sensor_type)
