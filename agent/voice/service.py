"""语音服务:
- STT: OpenAI Whisper (whisper-1) — 可降级为返回 501
- TTS: OpenAI Audio API (tts-1) — 浏览器侧用 Web Speech 作为兜底

设计为可替换接口,未来可接入百度/讯飞/Azure 等 Vertical SDK。
"""
from __future__ import annotations

import io
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def _has_key() -> bool:
    k = os.getenv("OPENAI_API_KEY", "").strip()
    if not k or k.startswith("sk-placeholder") or k == "sk-your-key-here":
        return False
    return len(k) >= 16


def _is_native_openai() -> bool:
    """智谱/OneAPI 等兼容端点不支持 Whisper/TTS,仅 OpenAI 官方支持。"""
    base = os.getenv("OPENAI_BASE_URL", "").strip().lower()
    if not base:
        return True
    return "openai.com" in base


def _client():
    from openai import OpenAI  # type: ignore

    kwargs: dict = {"api_key": os.getenv("OPENAI_API_KEY", "")}
    base = os.getenv("VOICE_BASE_URL", "").strip() or (
        os.getenv("OPENAI_BASE_URL", "").strip() if _is_native_openai() else ""
    )
    if base:
        kwargs["base_url"] = base
    return OpenAI(**kwargs)


async def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """语音转写。返回 {text, duration_ms?}"""
    if not _has_key():
        raise RuntimeError("STT 需要 OPENAI_API_KEY")
    if not _is_native_openai() and not os.getenv("VOICE_BASE_URL"):
        raise RuntimeError(
            "当前 LLM 端点不是 OpenAI 官方,智谱/兼容端点不提供 Whisper 服务;"
            "如需启用语音,请单独设置 VOICE_BASE_URL 与对应的 STT_MODEL"
        )
    try:
        client = _client()
        buf = io.BytesIO(audio_bytes)
        buf.name = filename
        resp = client.audio.transcriptions.create(
            model=os.getenv("STT_MODEL", "whisper-1"),
            file=buf,
        )
        text = getattr(resp, "text", "") or ""
        return {"text": text}
    except Exception as exc:
        logger.exception("transcribe failed")
        raise RuntimeError(f"STT 失败: {exc}") from exc


async def synthesize(text: str, voice: Optional[str] = None) -> bytes:
    """文本合成为 mp3 音频字节流。"""
    if not _has_key():
        raise RuntimeError("TTS 需要 OPENAI_API_KEY")
    if not _is_native_openai() and not os.getenv("VOICE_BASE_URL"):
        raise RuntimeError(
            "当前 LLM 端点不是 OpenAI 官方,智谱/兼容端点不提供 TTS 服务;"
            "前端会自动降级使用浏览器 SpeechSynthesis 语音"
        )
    try:
        client = _client()
        resp = client.audio.speech.create(
            model=os.getenv("TTS_MODEL", "tts-1"),
            voice=voice or os.getenv("TTS_VOICE", "alloy"),
            input=text[:3000],
        )
        if hasattr(resp, "read"):
            return resp.read()
        if hasattr(resp, "content"):
            return resp.content  # type: ignore
        return bytes(resp)
    except Exception as exc:
        logger.exception("synthesize failed")
        raise RuntimeError(f"TTS 失败: {exc}") from exc
