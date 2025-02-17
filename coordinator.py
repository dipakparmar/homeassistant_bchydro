"""Coordinator for the BC Hydro integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from bchydro import BCHydroApi
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(minutes=5)


class BCHydroCoordinator(DataUpdateCoordinator):
    """Class to manage fetching BC Hydro data."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="BC Hydro",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = BCHydroApi(entry.data["username"], entry.data["password"])

    async def _async_update_data(self):
        """Fetch data from BC Hydro."""
        try:
            await self.api.refresh()
            return {
                "latest_usage": await self.api.get_latest_usage(),
                "latest_cost": await self.api.get_latest_cost(),
                "billing_period_end": self.api.latest_interval.get("billing_period_end"),
            }
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err
