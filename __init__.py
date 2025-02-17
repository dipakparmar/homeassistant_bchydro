"""The BC Hydro integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import BCHydroCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up BC Hydro from a config entry."""
    coordinator = BCHydroCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(coordinator.async_update_listener))
    hass.data.setdefault("bchydro", {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data["bchydro"].pop(entry.entry_id)
    return unload_ok
