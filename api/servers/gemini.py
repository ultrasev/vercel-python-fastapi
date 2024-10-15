#!/usr/bin/env python
''' Convert Gemini API to OpenAI API format

Gemini API docs:
- https://ai.google.dev/gemini-api/docs/text-generation?lang=rest
'''

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import JSONResponse
import httpx
import typing
import codefast as cf
from typing import List, Dict, Optional
from .base import Message
import time

router = APIRouter()


GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"


class OpenAIProxyArgs(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    stream: bool = False
    temperature: float = 0.7
    top_p: float = 1
    n: int = 1
    max_tokens: Optional[int] = None
    presence_penalty: float = 0
    frequency_penalty: float = 0


class MessageConverter:
    def __init__(self, messages: List[Dict[str, str]]):
        self.messages = messages

    def convert(self) -> List[Dict[str, str]]:
        converted_messages = []
        for message in self.messages:
            role = "user" if message["role"] == "user" else "model"
            converted_messages.append({
                "role": role,
                "parts": [{"text": message["content"]}]
            })
        return converted_messages


def convert_gemini_to_openai_response(gemini_response: dict, model: str) -> dict:
    """Convert Gemini API response to OpenAI-compatible format."""
    return {
        "id": gemini_response.get("candidates", [{}])[0].get("content", {}).get("role", ""),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "usage": {
            "prompt_tokens": 0,  # Gemini doesn't provide token counts
            "completion_tokens": 0,
            "total_tokens": 0
        },
        "choices": [{
            "message": {
                "role": "assistant",
                "content": gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            },
            "finish_reason": "stop",
            "index": 0
        }]
    }


@router.post("/chat/completions")
async def proxy_chat_completions(
    args: OpenAIProxyArgs,
    authorization: str = Header(...),
):
    api_key = authorization.split(" ")[1]
    model = args.model

    if not api_key:
        raise HTTPException(status_code=400, detail="API key not provided")

    # Transform args into Gemini API format
    gemini_payload = {
        "contents": MessageConverter(args.messages).convert(),
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH"
            }
        ],
        "generationConfig": {
            "temperature": args.temperature,
            "maxOutputTokens": args.max_tokens,
            "topP": args.top_p,
            "topK": 10  # You might want to make this configurable
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GEMINI_ENDPOINT.format(model),
            json=gemini_payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
        )
        cf.info(response.status_code)

    if response.status_code != 200:
        return JSONResponse(content=response.json(), status_code=response.status_code)

    response_json = response.json()

    # Use the new conversion function
    openai_compatible_response = convert_gemini_to_openai_response(
        response_json, args.model)

    return JSONResponse(openai_compatible_response)
