"""Sample API Client."""

from __future__ import annotations

import asyncio
import base64
import socket
import time
from typing import Any

import aiohttp
import async_timeout

from custom_components.trading212.const import LOGGER, TOO_MANY_REQUESTS_STATUS_CODE


class IntegrationBlueprintApiClientError(Exception):
    """Exception to indicate a general API error."""


class IntegrationBlueprintApiClientCommunicationError(
    IntegrationBlueprintApiClientError,
):
    """Exception to indicate a communication error."""


class IntegrationBlueprintApiClientAuthenticationError(
    IntegrationBlueprintApiClientError,
):
    """Exception to indicate an authentication error."""


class IntegrationBlueprintApiClientTooManyRequestsError(
    IntegrationBlueprintApiClientError,
):
    """Exception to indicate too many requests (rate limiting)."""

    wait_seconds: int = 60

    def __init__(
        self,
        msg: str,
        wait_seconds: int,
    ) -> None:
        """Initialize."""
        super().__init__(msg)
        self.wait_seconds = wait_seconds


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    reset_header = response.headers.get("x-ratelimit-reset")
    reset_seconds = (
        int(reset_header) - int(time.time()) if reset_header is not None else "N/A"
    )
    LOGGER.debug(
        "Rate limit headers: Limit = %s, Period = %s, Remaining = %s, "
        "Reset = %s, Used = %s",
        response.headers.get("x-ratelimit-limit"),
        response.headers.get("x-ratelimit-period"),
        response.headers.get("x-ratelimit-remaining"),
        reset_seconds,
        response.headers.get("x-ratelimit-used"),
    )
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise IntegrationBlueprintApiClientAuthenticationError(
            msg,
        )
    if response.status == TOO_MANY_REQUESTS_STATUS_CODE:
        msg = "Too many requests (rate limited)"
        raise IntegrationBlueprintApiClientTooManyRequestsError(
            msg,
            wait_seconds=(
                int(response.headers["x-ratelimit-reset"]) - int(time.time())
                if "x-ratelimit-reset" in response.headers
                else 60
            ),
        )
    response.raise_for_status()


async def _check_wait_time(next_request_at: int) -> None:
    """Check if we need to wait before making the next request."""
    current_time = int(time.time())
    if current_time < next_request_at:
        wait_time = next_request_at - current_time + 1
        LOGGER.debug("Waiting %s seconds before making the next request", wait_time)
        await asyncio.sleep(wait_time)
        next_request_at = 0
    else:
        next_request_at = 0


class Trading212ApiClient:
    """Sample API Client."""

    next_request_at: int = 0

    def __init__(
        self,
        api_key_id: str,
        secret_key: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Sample API Client."""
        self._api_key_id = api_key_id
        self._secret_key = secret_key
        self._session = session

    def get_auth_header(self) -> Any:
        """Generate Authorization header."""
        credentials_string = f"{self._api_key_id}:{self._secret_key}"

        # 3. Encode the string to bytes, then Base64 encode it
        encoded_credentials = base64.b64encode(
            credentials_string.encode("utf-8")
        ).decode("utf-8")

        # 4. The final header value
        return f"Basic {encoded_credentials}"

    async def async_get_account_info(self) -> Any:
        """Get Account Information from the API."""
        return await self._api_wrapper(
            method="GET",
            url="https://live.trading212.com/api/v0/equity/account/info",
            headers={"Authorization": self.get_auth_header()},
        )

    async def async_get_account_cash(self) -> Any:
        """Get Account Cash Balance from the API."""
        return await self._api_wrapper(
            method="GET",
            url="https://live.trading212.com/api/v0/equity/account/cash",
            headers={"Authorization": self.get_auth_header()},
        )

    async def async_get_portfolio(self) -> Any:
        """Fetch all open positions."""
        return await self._api_wrapper(
            method="GET",
            url="https://live.trading212.com/api/v0/equity/portfolio",
            headers={"Authorization": self.get_auth_header()},
        )

    async def async_get_instruments(self) -> Any:
        """Fetch all open positions."""
        return await self._api_wrapper(
            method="GET",
            url="https://live.trading212.com/api/v0/equity/metadata/instruments",
            headers={"Authorization": self.get_auth_header()},
        )

    async def async_get_pies(self) -> Any:
        """Fetch all pies."""
        return await self._api_wrapper(
            method="GET",
            url="https://live.trading212.com/api/v0/equity/pies",
            headers={"Authorization": self.get_auth_header()},
        )

    async def async_get_pie(self, pie_id: int) -> Any:
        """Fetch a specific pie by ID."""
        return await self._api_wrapper(
            method="GET",
            url="https://live.trading212.com/api/v0/equity/pies/" + str(pie_id),
            headers={"Authorization": self.get_auth_header()},
        )

    async def async_get_orders(self) -> Any:
        """Fetch all orders."""
        result = await self._api_wrapper(
            method="GET",
            url="https://live.trading212.com/api/v0/equity/history/orders?cursor=0&ticker=SMH&limit=50",
            headers={"Authorization": self.get_auth_header()},
        )
        LOGGER.debug("Fetched %s orders", len(result["items"]))
        LOGGER.debug("Next page path = %s", result["nextPagePath"])

        return result

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
        retries: int = 10,
    ) -> Any:
        """Get information from the API."""
        try:
            await _check_wait_time(self.next_request_at)
            async with async_timeout.timeout(10):
                LOGGER.debug("%s %s", method, url)
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                remaining = response.headers.get("x-ratelimit-remaining")
                if remaining is not None and int(remaining) <= 1:
                    self.next_request_at = int(response.headers["x-ratelimit-reset"])

                _verify_response_or_raise(response)

                json = await response.json()
                LOGGER.debug("RESPONSE: %s", json)
                return json

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise IntegrationBlueprintApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise IntegrationBlueprintApiClientCommunicationError(
                msg,
            ) from exception
        except IntegrationBlueprintApiClientTooManyRequestsError as exception:
            if retries > 0:
                LOGGER.debug(
                    "Retrying after rate limit error, %s retries left. "
                    "Have to wait %s seconds...",
                    retries,
                    exception.wait_seconds,
                )
                await asyncio.sleep(
                    exception.wait_seconds
                )  # wait a bit before retrying
                return await self._api_wrapper(method, url, data, headers, retries - 1)
            raise  # propagate the rate limit error
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise IntegrationBlueprintApiClientError(
                msg,
            ) from exception
