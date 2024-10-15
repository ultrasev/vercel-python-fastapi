from pydantic import BaseModel, Field
import httpx
import asyncio
from typing import List, Dict, Optional


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


async def stream_openai_response(endpoint: str, payload: Dict, headers: Dict):
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", endpoint, json=payload, headers=headers) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield line + "\n\n"
                elif line.strip() == "data: [DONE]":
                    break
