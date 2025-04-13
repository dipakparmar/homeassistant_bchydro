"""Config flow for the BC Hydro integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .api import BCHydroApi


class BCHydroConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BC Hydro."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            username = user_input["username"]
            password = user_input["password"]

            try:
                # Validate credentials using the BCHydroApi
                api = BCHydroApi(username, password)
                await api.refresh()

                # If successful, create the entry
                return self.async_create_entry(
                    title="BC Hydro",
                    data={"username": username, "password": password},
                )
            except Exception:
                errors["base"] = "invalid_auth"

        data_schema = vol.Schema(
            {
                vol.Required("username"): str,
                vol.Required("password"): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return BCHydroOptionsFlowHandler(config_entry)


class BCHydroOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for BC Hydro."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
