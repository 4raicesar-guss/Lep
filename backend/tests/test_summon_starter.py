"""Tests de Fase 1: compra directa de unidades (summon) y Kit de Inicio."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from app.core.config import get_settings
from app.db.base import Base
from app.db.database import async_session, engine
from app.db.models import Player, UserBuilding, UserFormation, UserResource, UserUnit
from app.engine.data import SUMMON_COST
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

FAKE_BOT_TOKEN = "7777777777:AAFake_Test_Token_For_Unit_Tests_Only"


def _build_init_data(user: dict) -> str:
    params = {
        "auth_date": str(int(time.time())),
        "user": json.dumps(user, separators=(",", ":")),
        "query_id": "AAHdF6IQAAAAAN0XohA",
    }
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret = hmac.new(b"WebAppData", FAKE_BOT_TOKEN.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
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


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _units(telegram_id: int) -> list[UserUnit]:
    async with async_session() as session:
        res = await session.execute(select(UserUnit).where(UserUnit.user_id == telegram_id))
        return list(res.scalars().all())


# ---------------------------------------------------------------------------
# Starter Pack
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_starter_pack_new_player_gets_three_units():
    tid = 500000001
    init = _build_init_data({"id": tid, "first_name": "Nuevo"})

    async with _client() as client:
        r = await client.get("/api/player/state", headers={"X-Telegram-Init-Data": init})

    assert r.status_code == 200
    data = r.json()
    assert sorted(u["unit_id"] for u in data["units"]) == ["U01", "U03", "U06"]
    assert all(u["level"] == 1 and u["slot"] is None for u in data["units"])
    assert data["resources"]["grain"] == 500


@pytest.mark.asyncio
async def test_starter_pack_is_granted_only_once():
    tid = 500000002
    init = _build_init_data({"id": tid, "first_name": "Repetido"})

    async with _client() as client:
        for _ in range(3):
            r = await client.get("/api/player/state", headers={"X-Telegram-Init-Data": init})
            assert r.status_code == 200

    assert len(await _units(tid)) == 3


@pytest.mark.asyncio
async def test_existing_player_with_units_does_not_get_starter_pack():
    tid = 500000003
    init = _build_init_data({"id": tid, "first_name": "Veterano"})
    async with async_session() as session:
        session.add(Player(telegram_id=tid, first_name="Veterano"))
        session.add(UserUnit(id=uuid.uuid4(), user_id=tid, unit_id="U02", level=3))
        await session.commit()

    async with _client() as client:
        r = await client.get("/api/player/state", headers={"X-Telegram-Init-Data": init})

    assert r.status_code == 200
    units = r.json()["units"]
    assert len(units) == 1 and units[0]["unit_id"] == "U02"


# ---------------------------------------------------------------------------
# Summon
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summon_success_deducts_grain_and_creates_unit():
    tid = 500000010
    init = _build_init_data({"id": tid, "first_name": "Comprador"})
    headers = {"X-Telegram-Init-Data": init}

    async with _client() as client:
        await client.get("/api/player/state", headers=headers)  # starter pack + 500 grano
        r = await client.post("/api/units/summon", headers=headers, json={"unit_id": "U01"})

        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["cost"] == SUMMON_COST
        assert body["remaining_grain"] == 500 - SUMMON_COST
        assert body["unit"]["unit_id"] == "U01" and body["unit"]["level"] == 1

        state = (await client.get("/api/player/state", headers=headers)).json()

    assert len(state["units"]) == 4
    assert state["resources"]["grain"] == 500 - SUMMON_COST
    assert sorted(u["unit_id"] for u in state["units"]) == ["U01", "U01", "U03", "U06"]


@pytest.mark.asyncio
async def test_summon_lowercase_unit_id_is_accepted():
    tid = 500000011
    headers = {"X-Telegram-Init-Data": _build_init_data({"id": tid, "first_name": "Min"})}
    async with _client() as client:
        r = await client.post("/api/units/summon", headers=headers, json={"unit_id": "u04"})
    assert r.status_code == 200
    assert r.json()["unit"]["unit_id"] == "U04"


@pytest.mark.asyncio
async def test_summon_insufficient_grain_returns_400_and_changes_nothing():
    tid = 500000012
    headers = {"X-Telegram-Init-Data": _build_init_data({"id": tid, "first_name": "Pobre"})}
    async with _client() as client:
        await client.get("/api/player/state", headers=headers)
        async with async_session() as session:
            res = await session.scalar(select(UserResource).where(UserResource.user_id == tid))
            res.grain = SUMMON_COST - 1
            await session.commit()

        r = await client.post("/api/units/summon", headers=headers, json={"unit_id": "U02"})

    assert r.status_code == 400
    assert "Grano insuficiente" in r.json()["detail"]
    assert len(await _units(tid)) == 3
    async with async_session() as session:
        res = await session.scalar(select(UserResource).where(UserResource.user_id == tid))
        assert res.grain == SUMMON_COST - 1


@pytest.mark.asyncio
async def test_summon_invalid_unit_returns_400():
    tid = 500000013
    headers = {"X-Telegram-Init-Data": _build_init_data({"id": tid, "first_name": "X"})}
    async with _client() as client:
        r = await client.post("/api/units/summon", headers=headers, json={"unit_id": "U99"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_summon_requires_auth():
    async with _client() as client:
        r = await client.post(
            "/api/units/summon",
            headers={"X-Telegram-Init-Data": "hash=bad&auth_date=1&user=%7B%7D"},
            json={"unit_id": "U01"},
        )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_buy_three_then_merge_flow():
    """Flujo de la tienda: comprar hasta tener 3 U01 (el kit ya trae 1) y fusionarlos."""
    tid = 500000014
    headers = {"X-Telegram-Init-Data": _build_init_data({"id": tid, "first_name": "Merger"})}
    async with _client() as client:
        await client.get("/api/player/state", headers=headers)
        for _ in range(2):
            assert (
                await client.post("/api/units/summon", headers=headers, json={"unit_id": "U01"})
            ).status_code == 200

        inv = (await client.get("/api/units/inventory", headers=headers)).json()
        cerdos = [u["id"] for u in inv if u["unit_id"] == "U01"]
        assert len(cerdos) == 3

        r = await client.post("/api/units/merge", headers=headers, json={"unit_ids": cerdos})

    assert r.status_code == 200
    assert r.json()["new_level"] == 2
