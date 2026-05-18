from __future__ import annotations

from typing import Optional

import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from voice.service import synthesize, transcribe

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None


@router.post("/transcribe")
async def voice_transcribe(file: UploadFile = File(...)):
    try:
        data = await file.read()
        result = await transcribe(data, filename=file.filename or "audio.webm")
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc))


@router.post("/synthesize")
async def voice_synthesize(body: TTSRequest):
    if not body.text or not body.text.strip():
        raise HTTPException(400, "text 不能为空")
    try:
        audio = await synthesize(body.text, voice=body.voice)
    except RuntimeError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    return Response(content=audio, media_type="audio/mpeg")
