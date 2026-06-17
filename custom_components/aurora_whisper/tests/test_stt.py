"""Tests for the STT entity (requires the HA test stack)."""

from __future__ import annotations

from collections.abc import AsyncIterable
from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResultState,
)

from custom_components.aurora_whisper import AuroraWhisperRuntimeData
from custom_components.aurora_whisper.api import AuroraWhisperError
from custom_components.aurora_whisper.const import CONF_LANGUAGE, CONF_MODEL
from custom_components.aurora_whisper.stt import AuroraWhisperSttEntity

_METADATA = SpeechMetadata(
    language="sv",
    format=AudioFormats.WAV,
    codec=AudioCodecs.PCM,
    bit_rate=AudioBitRates.BITRATE_16,
    sample_rate=AudioSampleRates.SAMPLERATE_16000,
    channel=AudioChannels.CHANNEL_MONO,
)


async def _stream(chunks: list[bytes]) -> AsyncIterable[bytes]:
    for chunk in chunks:
        yield chunk


def _make_entity(transcribe: AsyncMock) -> AuroraWhisperSttEntity:
    entry = MagicMock()
    entry.entry_id = "abc123"
    entry.title = "Aurora Whisper (kb-whisper-large)"
    entry.data = {CONF_MODEL: "kb-whisper-large", CONF_LANGUAGE: "sv"}
    entry.options = {}
    client = MagicMock()
    client.async_transcribe = transcribe
    entry.runtime_data = AuroraWhisperRuntimeData(client=client)
    return AuroraWhisperSttEntity(entry)


def test_supported_languages_includes_configured() -> None:
    """The configured default language is always advertised."""
    entity = _make_entity(AsyncMock())
    assert "sv" in entity.supported_languages
    assert AudioFormats.WAV in entity.supported_formats
    assert AudioSampleRates.SAMPLERATE_16000 in entity.supported_sample_rates


@pytest.mark.asyncio
async def test_process_audio_success() -> None:
    """A successful transcription returns SUCCESS with the text."""
    transcribe = AsyncMock(return_value="hej världen")
    entity = _make_entity(transcribe)
    result = await entity.async_process_audio_stream(
        _METADATA, _stream([b"\x00\x01" * 100])
    )
    assert result.result == SpeechResultState.SUCCESS
    assert result.text == "hej världen"
    transcribe.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_audio_api_error() -> None:
    """An API error returns ERROR with no text (never raises)."""
    entity = _make_entity(AsyncMock(side_effect=AuroraWhisperError("boom")))
    result = await entity.async_process_audio_stream(
        _METADATA, _stream([b"\x00\x01" * 100])
    )
    assert result.result == SpeechResultState.ERROR
    assert result.text is None


@pytest.mark.asyncio
async def test_process_audio_empty_stream() -> None:
    """An empty stream short-circuits to ERROR without calling the API."""
    transcribe = AsyncMock()
    entity = _make_entity(transcribe)
    result = await entity.async_process_audio_stream(_METADATA, _stream([]))
    assert result.result == SpeechResultState.ERROR
    transcribe.assert_not_awaited()
