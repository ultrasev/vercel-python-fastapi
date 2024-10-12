#!/usr/bin/env python
from pydantic import BaseModel, Field
import httpx
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import FastAPI, File, Depends, Header, UploadFile, Form, HTTPException
from fastapi.routing import APIRouter
from openai import AsyncClient
from loguru import logger
import typing

router = APIRouter()
GROQ_TTS_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


class WhisperArgs(BaseModel):
    model: str = Field(default="whisper-large-v3")
    temperature: float = Field(default=0, ge=0, le=1)
    response_format: str = Field(default="json")
    language: typing.Optional[str] = None
    prompt: typing.Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "model": "whisper-large-v3",
                "temperature": 0,
                "response_format": "json",
                "language": "en"
            }
        }


@router.post("/transcribe/")
async def transcribe_audio(
    file: UploadFile = File(...),
    args: WhisperArgs = Depends(),
    authorization: str = Header(...)
):
    API_KEY = authorization.split(" ")[1]
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set")

    form_data = args.dict(exclude_none=True)
    form_data["temperature"] = str(form_data["temperature"])
    files = {
        "file": (file.filename, file.file, file.content_type)
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GROQ_TTS_URL,
                headers={'Authorization': authorization},
                data=form_data,
                files=files
            )
            response.raise_for_status()
            return JSONResponse(content=response.json())
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/stt/")
async def transcribe_audio(file: UploadFile = File(...), args: WhisperArgs = WhisperArgs(), authorization: str = Header(...)):
    api_key = authorization.split(" ")[1]
    client = AsyncClient(
        base_url="https://api.groq.com/openai/v1", api_key=api_key)
    contents = await file.read()
    transcription = await client.audio.transcriptions.create(
        file=(file.filename, contents),
        model=args.model,
        prompt=args.prompt,
        response_format=args.response_format,
        language=args.language,
        temperature=args.temperature
    )
    return {"transcription": transcription.text}


class ChatCompletionArgs(BaseModel):
    model: str
    messages: typing.List[typing.Dict[str, str]]
    temperature: float = Field(default=0.7, ge=0, le=1)


@router.post("/chat/completions")
async def chat_completions(
    args: ChatCompletionArgs,
    authorization: str = Header(...)
):
    api_key = authorization.split(" ")[1]
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": args.model,
        "messages": args.messages,
        "temperature": args.temperature
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return JSONResponse(data)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            return JSONResponse(content={"error": "chat failed"}, status_code=500)
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return JSONResponse(content={"error": "chat failed"}, status_code=500)
