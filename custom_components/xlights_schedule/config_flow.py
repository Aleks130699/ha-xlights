"""Config flow for the xLights Schedule integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
import aiohttp
import hashlib

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_PORT, DEFAULT_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): str,
        vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str, port: str) -> None:
        """Initialize."""
        self.host = host
        self.port = port

    async def authenticate(self, password: str) -> bool:
        """Test if we can authenticate with the host."""
        self.password = password
        self.base_url: str = f"http://{self.host}:{self.port}"
        credential_string = f"{self.host}{self.password}"
        credential_hash = hashlib.md5(credential_string.encode('UTF-8'))
        url = f"{self.base_url}/xScheduleLogin?Credential={credential_hash.hexdigest()}"
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)
            content = await response.json()
        if content["result"] == "ok":
            return True
        return False


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data[CONF_USERNAME], data[CONF_PASSWORD]
    # )

    hub = PlaceholderHub(data[CONF_HOST], data[CONF_PORT])

    if not await hub.authenticate(data[CONF_PASSWORD]):
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    # password = data[CONF_PASSWORD]
    # base_url: str = f"http://{host}:{port}"
    # url = f"{base_url}/xScheduleStash?Command=Retrieve&Key=uiSettings"
    # async with aiohttp.ClientSession() as session:
    #     response = await session.get(url)
    #     content = await response.json()
    # data[CONF_NAME] = content["webName"]
    # # Return info that you want to store in the config entry.
    # return {"name": content["webName"]}
    data[CONF_NAME] = "xLights"+" - "+host
    return {"name": data[CONF_NAME]}


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Falcon Pi Player."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["name"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
