#!/usr/bin/env python
from pydantic import BaseModel, Field
import httpx
from fastapi.responses import JSONResponse
from fastapi import FastAPI, File, Depends, Header, UploadFile, Form, HTTPException
from fastapi.routing import APIRouter
from openai import AsyncClient
import typing

router = APIRouter()


class GroqArgs(BaseModel):
    api_key: str
    model: str
    messages: typing.List[typing.Dict[str, str]]


@router.post("/v1")
async def test_groq(args: GroqArgs):
    client = AsyncClient(
        base_url="https://api.groq.com/openai/v1",
        api_key=args.api_key
    )
    return await client.chat.completions.create(
        model=args.model,
        messages=args.messages,
    )


class WhisperArgs(BaseModel):
    model: str = Field(default="whisper-large-v3")
    temperature: float = Field(default=0, ge=0, le=1)
    response_format: str = Field(default="json")
    language: typing.Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "model": "whisper-large-v3",
                "temperature": 0,
                "response_format": "json",
                "language": "en"
            }
        }


GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


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
                GROQ_API_URL,
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
