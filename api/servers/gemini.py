#!/usr/bin/env python
''' Convert Gemini API to OpenAI API format

Gemini API docs:
- https://ai.google.dev/gemini-api/docs/text-generation?lang=rest
'''
from loguru import logger
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import typing
from typing import List, Dict, Optional
from .base import Message
import time
import json
import re

router = APIRouter()


GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
GEMINI_STREAM_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{}:streamGenerateContent"


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


async def stream_gemini_response(model: str, payload: dict, api_key: str):
    text_pattern = re.compile(r'"text": "(.*?)"')

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            GEMINI_STREAM_ENDPOINT.format(model),
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
        ) as response:
            async for line in response.aiter_lines():
                line = line.strip()
                match = text_pattern.search(line)
                if match:
                    text_content = match.group(1)
                    # Unescape any escaped characters
                    text_content = text_content.encode().decode('unicode_escape')

                    openai_format = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "content": text_content
                            },
                            "finish_reason": None
                        }]
                    }

                    yield f"data: {json.dumps(openai_format)}\n\n"

    # Send a final chunk to indicate completion
    final_chunk = {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


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
            "topK": 10
        }
    }

    if args.stream:
        return StreamingResponse(stream_gemini_response(model, gemini_payload, api_key), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GEMINI_ENDPOINT.format(model),
                json=gemini_payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key
                }
            )
            logger.info(response.status_code)

            if response.status_code != 200:
                return JSONResponse(content=response.json(), status_code=response.status_code)

            response_json = response.json()

            # Use the new conversion function
            openai_compatible_response = convert_gemini_to_openai_response(
                response_json, args.model)

            return JSONResponse(openai_compatible_response)
