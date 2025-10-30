"""Adds config flow for Blueprint."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from custom_components.trading212.entity import get_instrument_name, get_pie_name

from .api import (
    IntegrationBlueprintApiClientAuthenticationError,
    IntegrationBlueprintApiClientCommunicationError,
    IntegrationBlueprintApiClientError,
    Trading212ApiClient,
)
from .const import (
    CONF_T212_ACCOUNT_ID,
    CONF_T212_ACCOUNT_NAME,
    CONF_T212_API_KEY_ID,
    CONF_T212_CURRENCY,
    CONF_T212_PIES,
    CONF_T212_SECRET_KEY,
    CONF_T212_SELECTED_PIES,
    CONF_T212_SELECTED_TICKERS,
    CONF_T212_TICKERS,
    DOMAIN,
    LOGGER,
)


class Trading212FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    data: dict[str, Any] = {}
    api_client: Trading212ApiClient

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                self.api_client = Trading212ApiClient(
                    api_key_id=user_input[CONF_T212_API_KEY_ID],
                    secret_key=user_input[CONF_T212_SECRET_KEY],
                    session=async_create_clientsession(self.hass),
                )
                LOGGER.debug("Testing Trading 212 credentials...")
                account_info = await self.api_client.async_get_account_info()
                LOGGER.debug("Account info: %s", account_info)
            except IntegrationBlueprintApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except IntegrationBlueprintApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except IntegrationBlueprintApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                # Store data and move to step 2
                self.data = {
                    CONF_T212_ACCOUNT_NAME: user_input[CONF_T212_ACCOUNT_NAME],
                    CONF_T212_API_KEY_ID: user_input[CONF_T212_API_KEY_ID],
                    CONF_T212_SECRET_KEY: user_input[CONF_T212_SECRET_KEY],
                    CONF_T212_ACCOUNT_ID: account_info["id"],
                    CONF_T212_CURRENCY: account_info.get("currencyCode"),
                    CONF_T212_TICKERS: [],
                    CONF_T212_PIES: [],
                }
                return await self.async_step_tickers()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_T212_ACCOUNT_NAME,
                        default=(
                            user_input or {CONF_T212_ACCOUNT_NAME: "Trading 212"}
                        ).get(CONF_T212_ACCOUNT_NAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_T212_API_KEY_ID): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_T212_SECRET_KEY): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def async_step_pies(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the second step for additional options."""
        if user_input is not None:
            self.data[CONF_T212_PIES] = user_input.get(CONF_T212_SELECTED_PIES)
            return self.async_create_entry(
                title=self.data[CONF_T212_ACCOUNT_NAME],
                data=self.data,
                options={},
            )

        pies = await self.api_client.async_get_pies()

        # Create checkbox-like options for each pie
        pie_options = [
            selector.SelectOptionDict(
                value=f"{pie['id']}",
                label=f"{await get_pie_name(self.api_client, pie['id'])}",
            )
            for pie in pies
        ]

        # Get pies that should be selected by default
        default_selected = [f"{pie['id']}" for pie in pies]

        return self.async_show_form(
            step_id=CONF_T212_PIES,
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_T212_SELECTED_PIES, default=default_selected
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=pie_options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                            sort=True,
                        ),
                    ),
                },
            ),
        )

    async def async_step_tickers(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the second step for additional options."""
        if user_input is not None:
            self.data[CONF_T212_TICKERS] = user_input.get(
                CONF_T212_SELECTED_TICKERS, []
            )
            return await self.async_step_pies()

        if len(self.data[CONF_T212_TICKERS]) == 0:
            portfolio = await self.api_client.async_get_portfolio()
            self.data[CONF_T212_TICKERS] = [item["ticker"] for item in portfolio]

        instruments = await self.api_client.async_get_instruments()

        # Create checkbox-like options for each ticker
        ticker_options = [
            selector.SelectOptionDict(
                value=ticker,
                label=f"{get_instrument_name(instruments, ticker)} ({ticker})",
            )
            for ticker in self.data[CONF_T212_TICKERS]
        ]

        # Get tickers that should be selected by default
        default_selected = list(self.data[CONF_T212_TICKERS])

        return self.async_show_form(
            step_id=CONF_T212_TICKERS,
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_T212_SELECTED_TICKERS, default=default_selected
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=ticker_options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        ),
                    ),
                },
            ),
        )
