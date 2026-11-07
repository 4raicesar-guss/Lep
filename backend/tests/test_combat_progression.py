"""
Tests para la progresión de oleadas y recompensas de combate:
- Gana oleada -> suma 100 de grano y current_wave pasa a 2
- GET /api/player/state devuelve current_wave
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.core.config import get_settings
from app.db.base import Base
from app.db.database import async_session, engine
from app.db.models import Player, UserBuilding, UserFormation, UserResource, UserUnit
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


@pytest.fixture(autouse=True)
def override_bot_token(monkeypatch):
    monkeypatch.setattr(get_settings(), "bot_token", FAKE_BOT_TOKEN)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        await session.execute(delete(UserFormation))
        await session.execute(delete(UserUnit))
        await session.execute(delete(UserBuilding))
        await session.execute(delete(UserResource))
        await session.execute(delete(Player))
        await session.commit()
    yield


@pytest.mark.asyncio
async def test_player_state_includes_current_wave():
    telegram_id = 999111222
    user = {"id": telegram_id, "first_name": "FarmerWave"}
    init_data = _build_init_data(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/player/state", headers={"X-Telegram-Init-Data": init_data})
        assert resp.status_code == 200
        data = resp.json()
        assert "current_wave" in data["player"]
        assert data["player"]["current_wave"] == 1


@pytest.mark.asyncio
async def test_simulate_combat_advances_wave_and_credits_grain():
    telegram_id = 999111333
    user = {"id": telegram_id, "first_name": "HeroFarmer"}
    init_data = _build_init_data(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Asegurar estado inicial vía /api/player/state
        state_resp = await client.get("/api/player/state", headers={"X-Telegram-Init-Data": init_data})
        assert state_resp.status_code == 200
        initial_grain = state_resp.json()["resources"]["grain"]
        assert state_resp.json()["player"]["current_wave"] == 1

        # 2. Formación fuerte garantizada para ganar Oleada 1 (Toro Bravo + Cerdo Nv 3)
        strong_formation = [
            {"unit_id": "U01", "level": 3, "position": 0},
            {"unit_id": "U02", "level": 3, "position": 1},
            {"unit_id": "U03", "level": 3, "position": 2},
        ]

        sim_resp = await client.post(
            "/api/combat/simulate",
            headers={"X-Telegram-Init-Data": init_data},
            json={"player_formation": strong_formation, "wave_number": 1},
        )
        assert sim_resp.status_code == 200
        sim_data = sim_resp.json()
        assert sim_data["winner"] == "player"
        assert sim_data["reward_grain"] == 100
        assert sim_data["new_total_grain"] == initial_grain + 100
        assert sim_data["next_wave"] == 2
        assert sim_data["villain"] is not None
        assert sim_data["villain"]["name"] == "Comandante Colmillo"

        # 3. Comprobar que en base de datos quedó persistido
        state_after = await client.get("/api/player/state", headers={"X-Telegram-Init-Data": init_data})
        assert state_after.status_code == 200
        after_data = state_after.json()
        assert after_data["player"]["current_wave"] == 2
        assert after_data["resources"]["grain"] == initial_grain + 100
