"""Sensor platform for Waffle City integration."""

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Waffle City sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]

    async_add_entities(
        [WaffleCityPackageSensor(coordinator, entry, api.user_id)],
        True,
    )


class WaffleCityPackageSensor(CoordinatorEntity, SensorEntity):
    """Sensor for pending packages."""

    _attr_has_entity_name = True
    _attr_translation_key = "pending_packages"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:package-variant"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        user_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._user_id = user_id
        self._attr_unique_id = f"{entry.entry_id}_pending_packages"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            translation_key="package_tracker",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> int:
        """Return the number of pending packages."""
        if self.coordinator.data is None:
            return 0
        return len(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        if not self.coordinator.data:
            return {"packages": []}

        packages = []
        for pkg in self.coordinator.data:
            package_info = {
                "package_id": pkg.get("package_id"),
                "community_name": pkg.get("community_name"),
                "family_name": pkg.get("family_name"),
                "user_name": pkg.get("user_name"),
                "places": ", ".join(pkg.get("places")) if pkg.get("places") else None,
                "thumbnail": pkg.get("thumbnail"),
                "created_at": pkg.get("create_at"),
            }
            # Only include non-None values
            packages.append({k: v for k, v in package_info.items() if v is not None})

        return {
            "packages": packages,
            "user_id": self._user_id,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
