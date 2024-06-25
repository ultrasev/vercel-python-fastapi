#!/usr/bin/env python
import os
import typing
from fastapi import File, UploadFile, Header, APIRouter
from pydantic import BaseModel
from groq import Groq

router = APIRouter()

class WhisperArgs(BaseModel):
    model: str
    prompt: typing.Optional[str] = None
    response_format: typing.Optional[str] = "json"
    language: typing.Optional[str] = "en"
    temperature: typing.Optional[float] = 0.0

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), args: WhisperArgs = WhisperArgs(), authorization: str = Header(...)):
    api_key = authorization.split(" ")[1]
    client = Groq(api_key=api_key)
    contents = await file.read()
    transcription = client.audio.transcriptions.create(
        file=(file.filename, contents),
        model=args.model,
        prompt=args.prompt,
        response_format=args.response_format,
        language=args.language,
        temperature=args.temperature
    )
    return {"transcription": transcription.text}
