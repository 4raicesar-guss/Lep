import asyncio
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.database import async_session, engine
from app.db.base import Base
from app.db.models import AnalyticsEvent
from app.main import app

FAKE_BOT_TOKEN = "7777777777:AAFake_Test_Token_For_Unit_Tests_Only"


def _build_init_data(user: dict) -> str:
    auth_date = str(int(time.time()))
    user_json = json.dumps(user, separators=(",", ":"))
    params = {
        "auth_date": auth_date,
        "user": user_json,
        "query_id": "AAHdF6IQAAAAAN0XohA",
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", FAKE_BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    params["hash"] = computed_hash
    return urlencode(params)


import pytest_asyncio

@pytest.fixture(autouse=True)
def override_bot_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "bot_token", FAKE_BOT_TOKEN)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        from sqlalchemy import delete
        await session.execute(delete(AnalyticsEvent))
        await session.commit()
    yield


@pytest.mark.asyncio
async def test_analytics_event_creation_and_server_time():
    user = {"id": 987654321, "first_name": "Tester", "username": "testuser"}
    init_data = _build_init_data(user)

    before_request = time.time()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/analytics/event",
            headers={"X-Telegram-Init-Data": init_data},
            json={
                "event_name": "test_button_click",
                "payload": {"screen": "home"},
            },
        )

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}

    # Dar un margen para que la background task complete la escritura
    await asyncio.sleep(0.1)

    async with async_session() as session:
        result = await session.execute(
            select(AnalyticsEvent).where(AnalyticsEvent.event_name == "test_button_click")
        )
        event = result.scalars().first()

    assert event is not None
    assert event.user_id == 987654321
    assert event.payload == {"screen": "home"}
    assert event.created_at is not None

    server_dt = event.created_at
    if server_dt.tzinfo is None:
        from datetime import timezone
        server_dt = server_dt.replace(tzinfo=timezone.utc)
    server_time = server_dt.timestamp()
    assert before_request - 5 <= server_time <= time.time() + 5
