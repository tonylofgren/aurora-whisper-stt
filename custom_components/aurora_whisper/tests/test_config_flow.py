"""Tests for the config flow (requires the HA test stack)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.aurora_whisper.api import (
    AuroraWhisperAuthError,
    AuroraWhisperError,
)
from custom_components.aurora_whisper.const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_LANGUAGE,
    CONF_MODEL,
    CONF_TIMEOUT,
    DOMAIN,
)

USER_INPUT = {
    CONF_BASE_URL: "https://api.test/v1",
    CONF_API_KEY: "sk-test",
    CONF_MODEL: "kb-whisper-large",
    CONF_LANGUAGE: "sv",
    CONF_TIMEOUT: 30,
}

_CHECK = (
    "custom_components.aurora_whisper.config_flow"
    ".AuroraWhisperClient.async_check_connection"
)


@pytest.mark.asyncio
async def test_user_flow_success(hass: HomeAssistant) -> None:
    """A valid connection creates the entry, titled with the model."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    with patch(_CHECK, new=AsyncMock(return_value=None)), patch(
        "custom_components.aurora_whisper.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Aurora Whisper (kb-whisper-large)"
    assert result2["data"] == USER_INPUT


@pytest.mark.asyncio
async def test_user_flow_invalid_auth(hass: HomeAssistant) -> None:
    """An auth error surfaces invalid_auth on the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(_CHECK, new=AsyncMock(side_effect=AuroraWhisperAuthError)):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


@pytest.mark.asyncio
async def test_user_flow_cannot_connect(hass: HomeAssistant) -> None:
    """A connection error surfaces cannot_connect on the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(_CHECK, new=AsyncMock(side_effect=AuroraWhisperError)):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
