# -*- coding: utf-8 -*-
"""展品讲解语音：服务端用 edge-tts 合成自然中文，前端直接播 mp3，
避开浏览器只能拿到 Huihui/Yaoyao 这类机械 SAPI 音的问题。"""
import hashlib
from collections import OrderedDict
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

router = APIRouter()

VOICE_DEFAULT = "zh-CN-XiaoxiaoNeural"
RATE_DEFAULT = "-4%"
MAX_TEXT = 320
CACHE_LIMIT = 300

_CACHE: "OrderedDict[str, bytes]" = OrderedDict()


class SpeakIn(BaseModel):
    text: str
    voice: Optional[str] = None
    rate: Optional[str] = None


@router.post("/speak")
async def speak(body: SpeakIn) -> Response:
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text required")
    if len(text) > MAX_TEXT:
        text = text[:MAX_TEXT]

    voice = (body.voice or VOICE_DEFAULT).strip()
    rate = (body.rate or RATE_DEFAULT).strip()

    key = hashlib.md5((voice + "|" + rate + "|" + text).encode("utf-8")).hexdigest()
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return Response(content=_CACHE[key], media_type="audio/mpeg",
                        headers={"Cache-Control": "public, max-age=86400"})

    try:
        import edge_tts
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail="tts unavailable: %s" % exc)

    buf = bytearray()
    try:
        comm = edge_tts.Communicate(text, voice, rate=rate)
        async for chunk in comm.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                buf.extend(chunk["data"])
    except Exception as exc:
        raise HTTPException(status_code=502, detail="tts failed: %s" % exc)

    if not buf:
        raise HTTPException(status_code=502, detail="tts empty")

    data = bytes(buf)
    _CACHE[key] = data
    if len(_CACHE) > CACHE_LIMIT:
        _CACHE.popitem(last=False)

    return Response(content=data, media_type="audio/mpeg",
                    headers={"Cache-Control": "public, max-age=86400"})


@router.get("/voices")
async def voices() -> dict:
    return {
        "voice": VOICE_DEFAULT,
        "rate": RATE_DEFAULT,
        "choices": [
            {"id": "zh-CN-XiaoxiaoNeural", "label": "晓晓 · 标准女声"},
            {"id": "zh-CN-XiaoyiNeural", "label": "晓伊 · 年轻女声"},
            {"id": "zh-CN-YunxiNeural", "label": "云希 · 青年男声"},
            {"id": "zh-CN-YunjianNeural", "label": "云健 · 浑厚男声"},
            {"id": "zh-CN-YunyeNeural", "label": "云野 · 稳重男声"},
            {"id": "zh-CN-liaoning-XiaobeiNeural", "label": "晓北 · 东北女声"},
        ],
    }
