"""Voice service helpers using Sarvam APIs for STT and TTS."""

import base64
import os
from typing import Any, Dict, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()


def _get_sarvam_config() -> Dict[str, str]:
    """Collect Sarvam config from environment variables."""
    return {
        "api_key": os.getenv("SARVAM_API_KEY", "").strip(),
        "base_url": os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai").rstrip("/"),
        "stt_path": os.getenv("SARVAM_STT_PATH", "/speech-to-text"),
        "tts_path": os.getenv("SARVAM_TTS_PATH", "/text-to-speech/stream"),
        "default_lang": os.getenv("SARVAM_DEFAULT_LANG", "en-IN"),
        "tts_model": os.getenv("SARVAM_TTS_MODEL", "bulbul:v3"),
        "tts_speaker": os.getenv("SARVAM_TTS_SPEAKER", "shubh"),
    }


def _build_headers(api_key: str) -> Dict[str, str]:
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is missing in .env")
    return {
        "api-subscription-key": api_key,
    }


def _extract_transcript(payload: Dict[str, Any]) -> str:
    """Handle common Sarvam STT response shapes."""
    candidates = [
        payload.get("transcript"),
        payload.get("text"),
        payload.get("result"),
        payload.get("output"),
    ]

    data_obj = payload.get("data")
    if isinstance(data_obj, dict):
        candidates.extend([
            data_obj.get("transcript"),
            data_obj.get("text"),
            data_obj.get("result"),
        ])

    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def transcribe_audio_bytes_via_sarvam(audio_bytes: bytes, language_code: str = "") -> str:
    """Send WAV audio bytes to Sarvam STT and return transcript text."""
    cfg = _get_sarvam_config()
    headers = _build_headers(cfg["api_key"])
    url = f"{cfg['base_url']}{cfg['stt_path']}"

    if not audio_bytes:
        raise ValueError("No audio data provided for transcription")

    files = {
        "file": ("voice.wav", audio_bytes, "audio/wav"),
    }

    attempts = [
        {"language_code": language_code or cfg["default_lang"]},
        {},
    ]
    last_payload: Dict[str, Any] = {}

    for attempt_idx, data in enumerate(attempts):
        response = requests.post(url, headers=headers, data=data, files=files, timeout=45)
        if response.status_code >= 400:
            raise RuntimeError(f"Sarvam STT failed ({response.status_code}): {response.text[:300]}")

        payload = response.json()
        last_payload = payload
        lang_used = data.get("language_code", "auto-detect")
        import sys
        print(f"[STT Attempt {attempt_idx+1}] Lang={lang_used}, AudioSize={len(audio_bytes)}B, ResponseKeys={list(payload.keys())}, Response={str(payload)[:500]}", file=sys.stderr)
        transcript = _extract_transcript(payload)
        if transcript:
            print(f"[STT Success] Got transcript: {transcript[:100]}", file=sys.stderr)
            return transcript

    print(f"[STT Failed] All attempts exhausted.", file=sys.stderr)
    raise ValueError("No speech detected — please speak clearly and try again")


def _extract_audio_from_response(payload: Dict[str, Any]) -> bytes:
    """Handle common Sarvam/base64 response shapes for TTS."""
    audio_value = payload.get("audio") or payload.get("audio_base64") or payload.get("data")

    if isinstance(audio_value, dict):
        audio_value = audio_value.get("audio") or audio_value.get("audio_base64")

    if isinstance(audio_value, list) and audio_value:
        first_item = audio_value[0]
        if isinstance(first_item, dict):
            audio_value = first_item.get("audio") or first_item.get("audio_base64")
        elif isinstance(first_item, str):
            audio_value = first_item

    if isinstance(audio_value, str):
        return base64.b64decode(audio_value)

    raise RuntimeError("Sarvam TTS response did not include decodable audio")


def synthesize_speech_via_sarvam(text: str, language_code: str = "") -> Tuple[bytes, str]:
    """Generate speech audio bytes from text via Sarvam TTS API."""
    cfg = _get_sarvam_config()
    headers = _build_headers(cfg["api_key"])
    headers["Content-Type"] = "application/json"
    url = f"{cfg['base_url']}{cfg['tts_path']}"

    clean_text = (text or "").strip()
    if not clean_text:
        raise ValueError("Text is empty for TTS")

    body = {
        "text": clean_text,
        "target_language_code": language_code or cfg["default_lang"],
        "model": cfg["tts_model"],
        "speaker": cfg["tts_speaker"],
        "speech_sample_rate": 22050,
        "output_audio_codec": "mp3",
        "enable_preprocessing": True,
    }

    with requests.post(url, headers=headers, json=body, stream=True, timeout=60) as response:
        if response.status_code >= 400:
            raise RuntimeError(f"Sarvam TTS failed ({response.status_code}): {response.text[:300]}")
        chunks = [chunk for chunk in response.iter_content(chunk_size=8192) if chunk]

    audio_bytes = b"".join(chunks)
    if not audio_bytes:
        raise RuntimeError("Sarvam TTS returned empty audio")
    return audio_bytes, "audio/mp3"
