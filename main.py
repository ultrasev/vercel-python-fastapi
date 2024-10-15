#!/usr/bin/env python3
from public.usage import USAGE as html
from api.hello import router as hello_router

from fastapi import FastAPI
from fastapi.responses import Response
from api.servers.groq import router as groq_router
from api.servers.openai import router as openai_router
from api.servers.gemini import router as gemini_router

app = FastAPI()

app.include_router(hello_router, prefix="/hello")
app.include_router(groq_router, prefix="/groq")
app.include_router(openai_router, prefix="/openai")
app.include_router(gemini_router, prefix="/gemini")


@app.get("/")
def _root():
    return Response(content=html, media_type="text/html")
