"""Adds config flow for Blueprint."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify

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
    CONF_T212_SECRET_KEY,
    DOMAIN,
    LOGGER,
)


class Trading212lowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                api_client = Trading212ApiClient(
                    api_key_id=user_input[CONF_T212_API_KEY_ID],
                    secret_key=user_input[CONF_T212_SECRET_KEY],
                    session=async_create_clientsession(self.hass),
                )
                LOGGER.debug("Testing Trading 212 credentials...")
                account_info = await api_client.async_get_account_info()
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
                LOGGER.debug("Account name: %s", user_input[CONF_T212_ACCOUNT_NAME])
                await self.async_set_unique_id(
                    ## Do NOT use this in production code
                    ## The unique_id should never be something that can change
                    ## https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
                    unique_id=slugify(user_input[CONF_T212_ACCOUNT_NAME])
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_T212_ACCOUNT_NAME],
                    data={
                        CONF_T212_ACCOUNT_NAME: user_input[CONF_T212_ACCOUNT_NAME],
                        CONF_T212_API_KEY_ID: user_input[CONF_T212_API_KEY_ID],
                        CONF_T212_SECRET_KEY: user_input[CONF_T212_SECRET_KEY],
                        CONF_T212_ACCOUNT_ID: account_info["id"],
                        CONF_T212_CURRENCY: account_info.get("currencyCode"),
                    },
                    options={},
                )

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
