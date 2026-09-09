import os

os.environ["CHAT_PROVIDER"] = "extractive"

import pytest
from typing import AsyncGenerator
import httpx
from httpx import ASGITransport
import pytest_asyncio
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an asynchronous HTTP client bound to the FastAPI ASGI application."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

