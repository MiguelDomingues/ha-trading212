"""Sensor platform for trading212."""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    EntityCategory,
    Platform,
    UnitOfTime,
)

from custom_components.trading212.const import (
    CONF_T212_API,
    CONF_T212_CASH,
    CONF_T212_CURRENCY,
    CONF_T212_INFO,
)
from custom_components.trading212.entity_description import Trading212Description

from .entity import IntegrationBlueprintEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import BlueprintDataUpdateCoordinator
    from .data import IntegrationBlueprintConfigEntry


@dataclass(frozen=True, kw_only=True)
class Trading212SensorDescription(Trading212Description, SensorEntityDescription):
    """Describes a Trading 212 sensor entity."""


def get_currency_code(entry: IntegrationBlueprintConfigEntry) -> str:
    """Get the currency code from the config entry, default to EUR."""
    return entry.data.get(CONF_T212_CURRENCY, "EUR")


def get_none(entry: IntegrationBlueprintConfigEntry) -> str:  # noqa: ARG001
    """Return an empty string, used as a placeholder for unit of measurement."""
    return ""


ENTITY_DESCRIPTIONS = (
    Trading212SensorDescription(
        key="free",
        name="Free Cash",
        api_field=CONF_T212_CASH,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        icon="mdi:cash-plus",
    ),
    Trading212SensorDescription(
        key="total",
        name="Total Cash",
        api_field=CONF_T212_CASH,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        icon="mdi:cash-multiple",
    ),
    Trading212SensorDescription(
        key="blocked",
        name="Blocked Cash",
        api_field=CONF_T212_CASH,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        icon="mdi:cash-lock",
    ),
    Trading212SensorDescription(
        key="invested",
        name="Invested Cash",
        api_field=CONF_T212_CASH,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        icon="mdi:cash-sync",
    ),
    Trading212SensorDescription(
        key="ppl",
        name="Potential Profit/Loss",
        api_field=CONF_T212_CASH,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        icon="mdi:cash-fast",
    ),
    Trading212SensorDescription(
        key="result",
        name="Realized Profit/Loss",
        api_field=CONF_T212_CASH,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="EUR",
        icon="mdi:cash-check",
    ),
    Trading212SensorDescription(
        key="id",
        name="Account ID",
        translation_key="account_id",
        api_field=CONF_T212_INFO,
        icon="mdi:id-card",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    Trading212SensorDescription(
        key="status",
        name="Status",
        translation_key="status",
        api_field=CONF_T212_API,
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        options=[
            "OK",
            "Too Many Requests",
            "Error",
        ],
        icon="mdi:lan-connect",
    ),
    Trading212SensorDescription(
        key="interval",
        translation_key="interval",
        name="Refresh Interval",
        api_field=CONF_T212_API,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:timer-outline",
    ),
    Trading212SensorDescription(
        key="duration",
        translation_key="duration",
        name="Refresh Duration",
        api_field=CONF_T212_API,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:timer-sand",
    ),
    Trading212SensorDescription(
        key="currencyCode",
        translation_key="currencyCode",
        name="Currency Code",
        api_field=CONF_T212_INFO,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:currency-sign",
    ),
)


@dataclass(frozen=True, kw_only=True)
class Trading212TickerFieldDescription:
    """Describes a Trading 212 ticker field."""

    ticker_field: str
    name: str
    native_unit_of_measurement: Callable[[IntegrationBlueprintConfigEntry], str]
    state_class: SensorStateClass
    device_class: SensorDeviceClass | None
    precision: int | None
    icon: str


TICKER_FIELDS = [
    Trading212TickerFieldDescription(
        ticker_field="quantity",
        name="Quantity",
        native_unit_of_measurement=get_none,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        precision=4,
        icon="mdi:sigma",
    ),
    Trading212TickerFieldDescription(
        ticker_field="averagePrice",
        name="Average Price",
        native_unit_of_measurement=get_currency_code,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
        precision=None,
        icon="mdi:cash-clock",
    ),
    Trading212TickerFieldDescription(
        ticker_field="currentPrice",
        name="Current Price",
        native_unit_of_measurement=get_currency_code,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
        precision=None,
        icon="mdi:cash-marker",
    ),
    Trading212TickerFieldDescription(
        ticker_field="ppl",
        name="Potential Profit/Loss",
        native_unit_of_measurement=get_currency_code,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
        precision=None,
        icon="mdi:cash-fast",
    ),
    Trading212TickerFieldDescription(
        ticker_field="pieQuantity",
        name="Pie Quantity",
        native_unit_of_measurement=get_none,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        precision=4,
        icon="mdi:pie-chart-pie-outline",
    ),
]


def ticker_get_field(
    coordinator: BlueprintDataUpdateCoordinator,
    ticker_name: str,
    field: str,
) -> Any:
    """Get the field of the ticker."""
    for ticker in coordinator.data["portfolio"]:
        if ticker["ticker"] == ticker_name:
            return ticker[field]

    return None


def get_value(
    api_field: str,
    key: str,
    coordinator: BlueprintDataUpdateCoordinator,
) -> Any:
    """Get the value of the sensor."""
    if api_field in coordinator.data:
        return coordinator.data[api_field].get(key)
    return None


def get_instrument_name(instruments: list[dict[str, Any]], ticker_symbol: str) -> str:
    """Get the instrument name for a given ticker symbol."""
    for instrument in instruments:
        if instrument.get("ticker") == ticker_symbol:
            return instrument.get("name", ticker_symbol)
    return ticker_symbol


def generate_ticker_field_sensors(
    portfolio: list[dict[str, Any]],
    instruments: list[dict[str, Any]],
    field: Trading212TickerFieldDescription,
    coordinator: BlueprintDataUpdateCoordinator,
    entry: IntegrationBlueprintConfigEntry,
) -> list[IntegrationBlueprintSensor]:
    """
    Generate sensor entities for each ticker in the portfolio for a specific field.

    Args:
        portfolio: List of portfolio ticker dictionaries.
        instruments: List of instrument dictionaries.
        field: The field to generate sensors for.
        coordinator: The data update coordinator.
        entry: The integration config entry.

    Returns:
        List of IntegrationBlueprintSensor entities for the specified field.

    """
    return [
        IntegrationBlueprintSensor(
            coordinator=coordinator,
            entity_description=Trading212SensorDescription(
                key=field.ticker_field,
                name=f"{field.name}",
                api_field="portfolio",
                state_class=field.state_class,
                device_class=field.device_class,
                native_unit_of_measurement=field.native_unit_of_measurement(entry),
                suggested_display_precision=field.precision,
            ),
            device_group=ticker["ticker"],
            device_name=get_instrument_name(instruments, ticker["ticker"]),
            value_fn=lambda coordinator, t=ticker: ticker_get_field(
                coordinator, t["ticker"], field.ticker_field
            ),
        )
        for ticker in portfolio
    ]


def generate_ticker_sensors(
    portfolio: list[dict[str, Any]],
    instruments: list[dict[str, Any]],
    coordinator: BlueprintDataUpdateCoordinator,
    entry: IntegrationBlueprintConfigEntry,
) -> list[IntegrationBlueprintSensor]:
    """
    Generate sensor entities for each field of each ticker in the portfolio.

    Args:
        portfolio: List of portfolio ticker dictionaries.
        instruments: List of instrument dictionaries.
        coordinator: The data update coordinator.
        entry: The integration config entry.

    Returns:
        List of IntegrationBlueprintSensor entities for the specified fields.

    """
    sensors = []
    for field in TICKER_FIELDS:  # initialFillDate
        sensors.extend(
            generate_ticker_field_sensors(
                portfolio,
                instruments,
                field,
                coordinator,
                entry,
            )
        )
    return sensors


@dataclass(frozen=True, kw_only=True)
class Trading212PieFieldDescription:
    """Describes a Trading 212 pie field."""

    pie_field: str
    name: str
    native_unit_of_measurement: Callable[[IntegrationBlueprintConfigEntry], str]
    state_class: SensorStateClass
    device_class: SensorDeviceClass | None
    precision: int | None
    icon: str


PIE_FIELDS = [
    Trading212PieFieldDescription(
        pie_field="cash",
        name="Cash",
        native_unit_of_measurement=get_currency_code,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
        precision=None,
        icon="",
    ),
]


def pie_get_field(
    coordinator: BlueprintDataUpdateCoordinator,
    ticker_name: str,
    field: str,
) -> Any:
    """Get the field of the pie."""
    for pie in coordinator.data["pies"]:
        if pie["id"] == ticker_name:
            return pie[field]

    return None


def generate_pie_field_sensors(
    pies: list[dict[str, Any]],
    field: Trading212PieFieldDescription,
    coordinator: BlueprintDataUpdateCoordinator,
    entry: IntegrationBlueprintConfigEntry,
) -> list[IntegrationBlueprintSensor]:
    """
    Generate sensor entities for each pie in the portfolio for a specific field.

    Args:
        pies: List of pie dictionaries.
        field: The field to generate sensors for.
        coordinator: The data update coordinator.
        entry: The integration config entry.

    Returns:
        List of IntegrationBlueprintSensor entities for the specified field.

    """
    return [
        IntegrationBlueprintSensor(
            coordinator=coordinator,
            entity_description=Trading212SensorDescription(
                key=field.pie_field,
                name=f"{field.name}",
                api_field="pies",
                state_class=field.state_class,
                device_class=field.device_class,
                native_unit_of_measurement=field.native_unit_of_measurement(entry),
                suggested_display_precision=field.precision,
            ),
            device_group=p["id"],
            device_name=coordinator.get_pie_name(p["id"]),
            value_fn=lambda coordinator, p=p: pie_get_field(
                coordinator, p["id"], field.pie_field
            ),
        )
        for p in pies
    ]


PIE_RESULT_FIELDS = [
    Trading212PieFieldDescription(
        pie_field="priceAvgInvestedValue",
        name="Invested Value",
        native_unit_of_measurement=get_currency_code,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
        precision=4,
        icon="",
    ),
    Trading212PieFieldDescription(
        pie_field="priceAvgValue",
        name="Value",
        native_unit_of_measurement=get_currency_code,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
        precision=4,
        icon="",
    ),
    Trading212PieFieldDescription(
        pie_field="priceAvgResult",
        name="Result",
        native_unit_of_measurement=get_currency_code,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.MONETARY,
        precision=4,
        icon="",
    ),
    Trading212PieFieldDescription(
        pie_field="priceAvgResultCoef",
        name="Result Coefficient",
        native_unit_of_measurement=get_none,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=None,
        precision=4,
        icon="",
    ),
]


def pie_get_result_field(
    coordinator: BlueprintDataUpdateCoordinator,
    ticker_name: str,
    field: str,
) -> Any:
    """Get the field of the pie."""
    for pie in coordinator.data["pies"]:
        if pie["id"] == ticker_name:
            return pie["result"][field]

    return None


def generate_pie_result_sensors(
    pies: list[dict[str, Any]],
    field: Trading212PieFieldDescription,
    coordinator: BlueprintDataUpdateCoordinator,
    entry: IntegrationBlueprintConfigEntry,
) -> list[IntegrationBlueprintSensor]:
    """
    Generate sensor entities for each pie in the portfolio for a specific field.

    Args:
        pies: List of pie dictionaries.
        field: The field to generate sensors for.
        coordinator: The data update coordinator.
        entry: The integration config entry.

    Returns:
        List of IntegrationBlueprintSensor entities for the specified field.

    """
    return [
        IntegrationBlueprintSensor(
            coordinator=coordinator,
            entity_description=Trading212SensorDescription(
                key=field.pie_field,
                name=f"{field.name}",
                api_field="pies",
                state_class=field.state_class,
                device_class=field.device_class,
                native_unit_of_measurement=field.native_unit_of_measurement(entry),
                suggested_display_precision=field.precision,
            ),
            device_group=p["id"],
            device_name=coordinator.get_pie_name(p["id"]),
            value_fn=lambda coordinator, p=p: pie_get_result_field(
                coordinator, p["id"], field.pie_field
            ),
        )
        for p in pies
    ]


def generate_pies_sensors(
    pies: list[dict[str, Any]],
    coordinator: BlueprintDataUpdateCoordinator,
    entry: IntegrationBlueprintConfigEntry,
) -> list[IntegrationBlueprintSensor]:
    """
    Generate sensor entities for each field of each pie in the portfolio.

    Args:
        pies: List of pie dictionaries.
        coordinator: The data update coordinator.
        entry: The integration config entry.

    Returns:
        List of IntegrationBlueprintSensor entities for the specified fields.

    """
    sensors = []
    for field in PIE_FIELDS:
        sensors.extend(
            generate_pie_field_sensors(
                pies,
                field,
                coordinator,
                entry,
            )
        )
    for field in PIE_RESULT_FIELDS:
        sensors.extend(
            generate_pie_result_sensors(
                pies,
                field,
                coordinator,
                entry,
            )
        )
    return sensors


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: IntegrationBlueprintConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    entities: list[IntegrationBlueprintSensor] = []

    entities.extend(
        IntegrationBlueprintSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
            device_group="account",
            device_name="Account",
            value_fn=functools.partial(
                get_value,
                entity_description.api_field,
                entity_description.key,
            ),
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )

    entities.extend(
        generate_ticker_sensors(
            entry.runtime_data.coordinator.data["portfolio"],
            entry.runtime_data.coordinator.data["instruments"],
            coordinator=entry.runtime_data.coordinator,
            entry=entry,
        )
    )

    entities.extend(
        generate_pies_sensors(
            entry.runtime_data.coordinator.data["pies"],
            entry.runtime_data.coordinator,
            entry=entry,
        )
    )

    async_add_entities(entities)


class IntegrationBlueprintSensor(IntegrationBlueprintEntity, SensorEntity):
    """Representation of a Trading 212 sensor."""

    entity_description: Trading212SensorDescription

    def __init__(
        self,
        coordinator: BlueprintDataUpdateCoordinator,
        entity_description: Trading212SensorDescription,
        device_group: str,
        device_name: str,
        value_fn: Callable[[BlueprintDataUpdateCoordinator], Any],
    ) -> None:
        """Initialize."""
        super().__init__(
            coordinator,
            entity_description.key,
            Platform.SENSOR,
            device_group,
            device_name=device_name,
        )
        self.entity_description = entity_description
        self.value_fn = value_fn

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self.value_fn(self.coordinator)
