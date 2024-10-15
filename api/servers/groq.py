from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import httpx
import asyncio
from typing import List, Dict, Optional
from .base import stream_openai_response, OpenAIProxyArgs, Message

router = APIRouter()
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


@router.post("/chat/completions")
async def proxy_chat_completions(args: OpenAIProxyArgs, authorization: str = Header(...)):
    api_key = authorization.split(" ")[1]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = args.dict(exclude_none=True)

    if args.stream:
        return StreamingResponse(stream_openai_response(GROQ_API_URL, payload, headers), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(GROQ_API_URL, json=payload, headers=headers)
                response.raise_for_status()
                return JSONResponse(response.json())
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code, detail=str(e.response.text))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
