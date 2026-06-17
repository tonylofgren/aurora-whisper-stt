"""Standalone unit tests for the PCM->WAV wrapper.

These deliberately avoid importing the integration package (which pulls in
Home Assistant). The audio module is loaded directly from its file path so the
tests run with nothing but the Python standard library plus pytest.
"""

from __future__ import annotations

import importlib.util
import io
import wave
from pathlib import Path

_AUDIO_PATH = Path(__file__).resolve().parents[1] / "audio.py"
_spec = importlib.util.spec_from_file_location("aurora_whisper_audio", _AUDIO_PATH)
assert _spec and _spec.loader
audio = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audio)


def test_pcm_to_wav_has_canonical_header() -> None:
    """A canonical 16-bit PCM WAV has a 44-byte RIFF/WAVE header."""
    pcm = b"\x01\x02" * 1600
    data = audio.pcm_to_wav(pcm)
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WAVE"
    assert len(data) == 44 + len(pcm)


def test_pcm_to_wav_roundtrip() -> None:
    """The WAV must declare mono/16 kHz/16-bit and preserve the samples."""
    pcm = bytes(range(256)) * 8
    data = audio.pcm_to_wav(pcm)
    with wave.open(io.BytesIO(data), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
        assert wav.getsampwidth() == 2
        assert wav.getnframes() == len(pcm) // 2
        assert wav.readframes(wav.getnframes()) == pcm


def test_pcm_to_wav_empty() -> None:
    """An empty PCM buffer still yields a valid (header-only) WAV."""
    data = audio.pcm_to_wav(b"")
    assert data[:4] == b"RIFF"
    assert len(data) == 44
