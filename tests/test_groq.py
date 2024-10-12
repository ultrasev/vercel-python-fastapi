import asyncio
import pytest
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
import aiohttp
import random
load_dotenv()


def api_endpoint():
    env = os.environ.get('ENV', 'development')
    if env == 'production':
        return ""
    elif env == 'development':
        return "http://192.168.31.46:3000/groq"
    else:
        raise ValueError(f"Invalid environment: {env}")

BASE_URL = api_endpoint()
async def make_request(api_key: str,
                       model: str,
                       supplier: str,
                       query: str = "what is the result of 2*21"):
    client = AsyncOpenAI(base_url=BASE_URL, api_key=api_key)
    query += random.randint(1, 1000) * ' '  # avoid cached result
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant。"},
            {"role": "user", "content": query}
        ],
        temperature=0.7,
        top_p=1,
        max_tokens=20
    )
    print(type(response), response)
    return response.choices[0].message.content


@pytest.mark.asyncio
async def test_groq():
    response = await make_request(
        api_key=os.environ["GROQ_API_KEY"],
        model="llama3-70b-8192",
        supplier="groq"
    )
    assert '42' in response
