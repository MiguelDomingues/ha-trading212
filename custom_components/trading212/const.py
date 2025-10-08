"""Constants for Trading 212."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "trading212"
ATTRIBUTION = "Data provided by https://www.trading212.com/ API"

CONF_T212_ACCOUNT_NAME = "account_name"
CONF_T212_API_KEY_ID = "api_key_id"
CONF_T212_ACCOUNT_ID = "account_id"
CONF_T212_CURRENCY = "currency"
CONF_T212_SECRET_KEY = "secret_key"  # noqa: S105
CONF_T212_INTERVAL_SECONDS = 60

CONF_T212_INFO = "info"
CONF_T212_CASH = "cash"
CONF_T212_PORTFOLIO = "portfolio"
CONF_T212_INSTRUMENTS = "instruments"
CONF_T212_PIES = "pies"
CONF_T212_PIES_DATA = "pies_data"
CONF_T212_ORDERS = "orders"
CONF_T212_API = "api"
CONF_T212_STATUS = "status"
CONF_T212_INTERVAL = "interval"
CONF_T212_DURATION = "duration"

ENTITY_PREFIX = "t212"

TOO_MANY_REQUESTS_STATUS_CODE = 429
