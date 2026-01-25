"""The Waffle City integration."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TokenData, WaffleCityApi, WaffleCityApiError, WaffleCityAuthError
from .const import (
    CONF_COUNTRY_CODE,
    CONF_PASSWORD,
    CONF_PHONE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]
STORAGE_VERSION = 1


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waffle City from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Set up token storage
    store: Store[dict] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")

    async def save_token(token_data: TokenData) -> None:
        """Save token data to storage."""
        await store.async_save(dict(token_data))
        _LOGGER.debug("Token data saved to storage")

    session = async_get_clientsession(hass)
    api = WaffleCityApi(
        phone=entry.data[CONF_PHONE],
        password=entry.data[CONF_PASSWORD],
        country_code=entry.data.get(CONF_COUNTRY_CODE, "TW"),
        session=session,
        on_token_update=lambda data: hass.async_create_task(save_token(data)),
    )

    # Try to restore saved token
    stored_data = await store.async_load()
    if stored_data:
        _LOGGER.debug("Found stored token, attempting to restore")
        api.set_token_data(TokenData(
            token=stored_data["token"],
            user_id=stored_data["user_id"],
            community_ids=stored_data["community_ids"],
        ))

        # Validate the restored token
        if await api.validate_token():
            _LOGGER.info("Restored and validated saved token")
        else:
            _LOGGER.info("Saved token invalid, performing fresh authentication")
            try:
                await api.authenticate()
            except (WaffleCityAuthError, WaffleCityApiError) as err:
                _LOGGER.error("Failed to authenticate with Waffle City: %s", err)
                return False
    else:
        _LOGGER.debug("No stored token found, performing fresh authentication")
        try:
            await api.authenticate()
        except (WaffleCityAuthError, WaffleCityApiError) as err:
            _LOGGER.error("Failed to authenticate with Waffle City: %s", err)
            return False

    async def async_update_data():
        """Fetch data from API."""
        try:
            return await api.get_pending_packages()
        except WaffleCityAuthError as err:
            # Try to re-authenticate
            try:
                await api.authenticate()
                return await api.get_pending_packages()
            except (WaffleCityAuthError, WaffleCityApiError) as auth_err:
                raise UpdateFailed(f"Authentication failed: {auth_err}") from auth_err
        except WaffleCityApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "store": store,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove a config entry and clean up storage."""
    store: Store[dict] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
    await store.async_remove()
    _LOGGER.debug("Removed stored token data for entry %s", entry.entry_id)
