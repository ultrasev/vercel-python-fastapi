import asyncio
import pytest
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
import random
from loguru import logger
load_dotenv()


def api_endpoint():
    env = os.environ.get('ENV', 'development')
    if env == 'production':
        return "https://llmapi-69qqyvcj2-slippertopia.vercel.app/proxy/api.groq.com/openai/v1"
    elif env == 'development':
        return "http://192.168.31.46:3000"
    else:
        raise ValueError(f"Invalid environment: {env}")


BASE_URL = api_endpoint()
logger.info(f"BASE_URL: {BASE_URL}")


async def make_request(api_key: str,
                       model: str,
                       supplier: str,
                       query: str = "what is the result of 2*21"):
    client = AsyncOpenAI(base_url=BASE_URL + f"/{supplier}", api_key=api_key)
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
    await make_request(
        supplier="groq",
        api_key=os.environ["GROQ_API_KEY"],
        model="llama3-70b-8192"
    )


@pytest.mark.asyncio
async def test_openai():
    await make_request(
        supplier="openai",
        api_key=os.environ["OPENAI_API_KEY"],
        model="gpt-4o-mini"
    )
#
