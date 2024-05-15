#!/usr/bin/env python3
from public.usage import USAGE as html
from api.hello import router as hello_router
from fastapi import FastAPI
from fastapi.responses import Response
app = FastAPI()

app.include_router(hello_router, prefix="/hello")


@app.get("/")
def _root():
    return Response(content=html, media_type="text/html")
