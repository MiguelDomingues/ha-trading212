"""Trading 212 entity description."""

from dataclasses import dataclass

from homeassistant.helpers.entity import EntityDescription


@dataclass(frozen=True, kw_only=True)
class Trading212Description(EntityDescription):
    """Describes a Trading 212 entity."""

    api_field: str
