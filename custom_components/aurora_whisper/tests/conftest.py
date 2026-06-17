"""Shared fixtures for the tests.

The Home Assistant based tests (test_api/test_config_flow/test_stt) need the HA
test stack (see requirements_test.txt): homeassistant,
pytest-homeassistant-custom-component, aioresponses.

test_audio.py is intentionally standalone and runs on the stdlib + pytest alone,
so the HA plugin is only registered when it is actually installed. That keeps the
core WAV unit tests runnable without pulling in Home Assistant.
"""

from __future__ import annotations

import importlib.util

import pytest

_HAS_HA = (
    importlib.util.find_spec("pytest_homeassistant_custom_component") is not None
)

if _HAS_HA:
    pytest_plugins = ["pytest_homeassistant_custom_component"]

    @pytest.fixture(autouse=True)
    def auto_enable_custom_integrations(enable_custom_integrations):
        """Enable loading of the custom integration in every HA test."""
        yield
