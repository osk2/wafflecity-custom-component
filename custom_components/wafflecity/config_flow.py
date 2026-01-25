"""Config flow for Waffle City integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WaffleCityApi, WaffleCityApiError, WaffleCityAuthError
from .const import (
    CONF_COUNTRY_CODE,
    CONF_PASSWORD,
    CONF_PHONE,
    COUNTRY_CODES,
    DEFAULT_COUNTRY_CODE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class WaffleCityConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Waffle City."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate credentials
            session = async_get_clientsession(self.hass)
            api = WaffleCityApi(
                phone=user_input[CONF_PHONE],
                password=user_input[CONF_PASSWORD],
                country_code=user_input.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE),
                session=session,
            )

            try:
                await api.authenticate()

                # Use phone as unique ID
                await self.async_set_unique_id(user_input[CONF_PHONE])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Waffle City ({user_input[CONF_PHONE]})",
                    data=user_input,
                )

            except WaffleCityAuthError:
                errors["base"] = "invalid_auth"
            except WaffleCityApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PHONE): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_COUNTRY_CODE, default=DEFAULT_COUNTRY_CODE
                    ): vol.In(COUNTRY_CODES),
                }
            ),
            errors=errors,
        )
