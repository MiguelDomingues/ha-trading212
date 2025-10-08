"""BlueprintEntity class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_T212_ACCOUNT_NAME,
    ENTITY_PREFIX,
)
from .coordinator import BlueprintDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.const import Platform


def get_unique_id(account: str, device_group: str, key: str) -> str:
    """Get the unique ID."""
    return f"{ENTITY_PREFIX}_{account}_{device_group}_{key}".lower().replace(" ", "_")


def get_entity_id(platform: Platform, account: str, device_group: str, key: str) -> str:
    """Get the entity ID."""
    return f"{platform}.{get_unique_id(account, device_group, key)}".lower().replace(
        " ", "_"
    )


class IntegrationBlueprintEntity(CoordinatorEntity[BlueprintDataUpdateCoordinator]):
    """BlueprintEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: BlueprintDataUpdateCoordinator,
        context: str,
        platform: Platform,
        device_group: str,
        device_name: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.entity_id = get_entity_id(
            platform,
            coordinator.config_entry.data[CONF_T212_ACCOUNT_NAME],
            device_group,
            context,
        )
        self._attr_unique_id = get_unique_id(
            coordinator.config_entry.data[CONF_T212_ACCOUNT_NAME], device_group, context
        )
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    f"{coordinator.config_entry.entry_id}_{device_group}",
                ),
            },
            name=f"{device_name if device_name else device_group}",
        )
