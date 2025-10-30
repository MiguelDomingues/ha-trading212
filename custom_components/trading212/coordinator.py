"""DataUpdateCoordinator for trading212."""

from __future__ import annotations

import time
from datetime import timedelta
from math import ceil
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.trading212.const import (
    CONF_T212_API,
    CONF_T212_CASH,
    CONF_T212_DURATION,
    CONF_T212_INSTRUMENTS,
    CONF_T212_INTERVAL,
    CONF_T212_INTERVAL_SECONDS,
    CONF_T212_PIES,
    CONF_T212_PORTFOLIO,
    CONF_T212_STATUS,
    CONF_T212_TICKERS,
    LOGGER,
)

from .api import (
    IntegrationBlueprintApiClientAuthenticationError,
    IntegrationBlueprintApiClientCommunicationError,
    IntegrationBlueprintApiClientError,
    Trading212ApiClient,
)

if TYPE_CHECKING:
    from .data import IntegrationBlueprintConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class BlueprintDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: IntegrationBlueprintConfigEntry
    update_interval: timedelta
    pie_name: dict[str, str]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the coordinator with runtime data and pie name cache."""
        super().__init__(*args, **kwargs)
        self.pie_name = {}

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            LOGGER.debug("Fetching data from Trading 212 API...")
            start_time = time.time()
            too_many_requests = False
            api_client = self.config_entry.runtime_data.client

            cash = await api_client.async_get_account_cash()

            if len(self.config_entry.data.get(CONF_T212_TICKERS, [])) > 0:
                portfolio = await api_client.async_get_portfolio()
            else:
                portfolio = []

            if portfolio and (
                self.data is None or CONF_T212_INSTRUMENTS not in self.data
            ):
                instruments = await api_client.async_get_instruments()
                # Filter instruments to only those whose ticker is in portfolio
                portfolio_tickers = {item["ticker"] for item in portfolio}
                instruments = [
                    inst for inst in instruments if inst["ticker"] in portfolio_tickers
                ]
            else:
                instruments = (
                    self.data[CONF_T212_INSTRUMENTS]
                    if self.data and CONF_T212_INSTRUMENTS in self.data
                    else []
                )

            if len(self.config_entry.data.get(CONF_T212_PIES, [])) > 0:
                pies = await api_client.async_get_pies()
                await self.cache_pie_names(api_client, pies)
            else:
                pies = []

            inv_duration = time.time() - start_time
            self.update_interval = max(
                timedelta(seconds=ceil(CONF_T212_INTERVAL_SECONDS - inv_duration)),
                timedelta(seconds=1),
            )
            LOGGER.debug(
                "Next update in %s seconds", self.update_interval.total_seconds()
            )

            return {
                CONF_T212_CASH: cash,
                CONF_T212_PORTFOLIO: portfolio,
                CONF_T212_INSTRUMENTS: instruments,
                CONF_T212_PIES: pies,
                CONF_T212_API: {
                    CONF_T212_STATUS: (
                        "OK" if not too_many_requests else "Too Many Requests"
                    ),
                    CONF_T212_INTERVAL: self.update_interval.total_seconds(),
                    CONF_T212_DURATION: round(time.time() - start_time, 2),
                },
            }
        except IntegrationBlueprintApiClientCommunicationError as exception:
            LOGGER.error("Communication Error: %s", exception)
            return {
                CONF_T212_CASH: {},
                CONF_T212_API: {
                    CONF_T212_STATUS: "Error",
                    CONF_T212_INTERVAL: self.update_interval.total_seconds(),
                    CONF_T212_DURATION: None,
                },
            }
        except IntegrationBlueprintApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationBlueprintApiClientError as exception:
            raise UpdateFailed(exception) from exception
        except Exception as exception:  # noqa: BLE001
            LOGGER.error("Unexpected error occurred: %s", exception)
            return {
                CONF_T212_CASH: {},
                CONF_T212_API: {
                    CONF_T212_STATUS: "Error",
                    CONF_T212_INTERVAL: self.update_interval.total_seconds(),
                    CONF_T212_DURATION: None,
                },
            }

    async def cache_pie_names(
        self, api_client: Trading212ApiClient, pies: list[dict]
    ) -> None:
        """Cache the names of the pies."""
        for pie in pies:
            if pie[
                "id"
            ] not in self.pie_name and f"{pie['id']}" in self.config_entry.data.get(
                CONF_T212_PIES, []
            ):
                pie_data = await api_client.async_get_pie(pie["id"])
                self.pie_name[pie["id"]] = pie_data["settings"]["name"]

    def get_pie_name(self, pie_id: str) -> str:
        """Get the name of a pie by its ID."""
        if self.pie_name.get(pie_id):
            return self.pie_name[pie_id]

        return pie_id
