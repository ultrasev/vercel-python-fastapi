from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import httpx
import asyncio
from typing import List, Dict, Optional

router = APIRouter()
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class Message(BaseModel):
    role: str
    content: str


class OpenAIProxyArgs(BaseModel):
    model: str
    messages: List[Message]
    stream: bool = False
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=1, ge=0, le=1)
    n: int = Field(default=1, ge=1)
    max_tokens: Optional[int] = None
    presence_penalty: float = Field(default=0, ge=-2, le=2)
    frequency_penalty: float = Field(default=0, ge=-2, le=2)


async def stream_openai_response(payload, headers):
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", OPENAI_API_URL, json=payload, headers=headers) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield line + "\n\n"
                elif line.strip() == "data: [DONE]":
                    break


@router.post("/chat/completions")
async def proxy_chat_completions(args: OpenAIProxyArgs, authorization: str = Header(...)):
    api_key = authorization.split(" ")[1]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = args.dict(exclude_none=True)

    if args.stream:
        return StreamingResponse(stream_openai_response(payload, headers), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(OPENAI_API_URL, json=payload, headers=headers)
                response.raise_for_status()
                return JSONResponse(response.json())
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code, detail=str(e.response.text))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
