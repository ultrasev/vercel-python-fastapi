#!/usr/bin/env python
from fastapi.routing import APIRouter
import random 
router = APIRouter()


@router.get("/")
def read_root():
    return {"number": random.randint(1, 100)}


