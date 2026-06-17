"""Tests for the async Whisper API client (requires the HA test stack)."""

from __future__ import annotations

import aiohttp
from aioresponses import aioresponses
import pytest

from custom_components.aurora_whisper.api import (
    AuroraWhisperAuthError,
    AuroraWhisperClient,
    AuroraWhisperError,
)

BASE_URL = "https://api.test/v1"
TRANSCRIBE_URL = f"{BASE_URL}/audio/transcriptions"
MODELS_URL = f"{BASE_URL}/models"


@pytest.mark.asyncio
async def test_transcribe_success() -> None:
    """A 200 with {'text': ...} returns trimmed text."""
    with aioresponses() as mocked:
        mocked.post(TRANSCRIBE_URL, payload={"text": "  hej världen  "})
        async with aiohttp.ClientSession() as session:
            client = AuroraWhisperClient(session, BASE_URL, "sk-test", 30)
            text = await client.async_transcribe(b"RIFFxxxx", model="whisper-1")
    assert text == "hej världen"


@pytest.mark.asyncio
async def test_transcribe_auth_error() -> None:
    """A 401 raises AuroraWhisperAuthError."""
    with aioresponses() as mocked:
        mocked.post(TRANSCRIBE_URL, status=401)
        async with aiohttp.ClientSession() as session:
            client = AuroraWhisperClient(session, BASE_URL, "bad", 30)
            with pytest.raises(AuroraWhisperAuthError):
                await client.async_transcribe(b"RIFFxxxx", model="whisper-1")


@pytest.mark.asyncio
async def test_transcribe_server_error() -> None:
    """A 500 raises AuroraWhisperError."""
    with aioresponses() as mocked:
        mocked.post(TRANSCRIBE_URL, status=500, body="boom")
        async with aiohttp.ClientSession() as session:
            client = AuroraWhisperClient(session, BASE_URL, "sk-test", 30)
            with pytest.raises(AuroraWhisperError):
                await client.async_transcribe(b"RIFFxxxx", model="whisper-1")


@pytest.mark.asyncio
async def test_check_connection_ok() -> None:
    """A 200 from /models passes."""
    with aioresponses() as mocked:
        mocked.get(MODELS_URL, status=200, payload={"data": []})
        async with aiohttp.ClientSession() as session:
            client = AuroraWhisperClient(session, BASE_URL, "sk-test", 30)
            await client.async_check_connection()


@pytest.mark.asyncio
async def test_check_connection_tolerates_missing_models() -> None:
    """A 404 from /models is tolerated (server lacks the endpoint)."""
    with aioresponses() as mocked:
        mocked.get(MODELS_URL, status=404)
        async with aiohttp.ClientSession() as session:
            client = AuroraWhisperClient(session, BASE_URL, "sk-test", 30)
            await client.async_check_connection()


@pytest.mark.asyncio
async def test_check_connection_auth_error() -> None:
    """A 403 from /models raises AuroraWhisperAuthError."""
    with aioresponses() as mocked:
        mocked.get(MODELS_URL, status=403)
        async with aiohttp.ClientSession() as session:
            client = AuroraWhisperClient(session, BASE_URL, "bad", 30)
            with pytest.raises(AuroraWhisperAuthError):
                await client.async_check_connection()
