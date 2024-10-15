#!/usr/bin/env python3
from public.usage import USAGE as html
from api.hello import router as hello_router
from api.random import router as random_router


from api.servers.groq import router as groq_router
from fastapi import FastAPI
from fastapi.responses import Response
from api.servers.openai import router as openai_router

app = FastAPI()

app.include_router(hello_router, prefix="/hello")
app.include_router(random_router, prefix="/random")
app.include_router(groq_router, prefix="/groq")
app.include_router(openai_router, prefix="/openai")


@app.get("/")
def _root():
    return Response(content=html, media_type="text/html")
