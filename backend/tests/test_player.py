import hashlib
import hmac
import json
import time
import uuid
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
async def test_get_player_state_unauthorized_missing_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/player/state")
    assert response.status_code in (401, 422)


@pytest.mark.asyncio
async def test_get_player_state_unauthorized_invalid_hash():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/player/state",
            headers={"X-Telegram-Init-Data": "query_id=123&user=%7B%7D&hash=invalid_hash"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_player_state_creates_initial_state_for_new_player():
    user = {"id": 123456789, "first_name": "Gaucho", "username": "el_gaucho"}
    init_data = _build_init_data(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/player/state",
            headers={"X-Telegram-Init-Data": init_data},
        )

    assert response.status_code == 200
    data = response.json()

    # Validar estructura básica
    assert data["player"]["telegram_id"] == 123456789
    assert data["player"]["first_name"] == "Gaucho"
    assert data["player"]["username"] == "el_gaucho"

    # Recursos por defecto (500 grano)
    assert data["resources"]["grain"] == 500
    assert data["resources"]["last_collected_at"] is not None

    # Edificios por defecto (nivel 1)
    assert data["buildings"]["silo_level"] == 1
    assert data["buildings"]["galpon_level"] == 1
    assert data["buildings"]["boyero_level"] == 1

    # Kit de Inicio: 1x U01, 1x U03, 1x U06, todas en el banco (sin slot)
    assert sorted(u["unit_id"] for u in data["units"]) == ["U01", "U03", "U06"]
    assert all(u["slot"] is None for u in data["units"])

    # Formación con los 9 slots en null
    slots = data["formation"]["slots"]
    assert len(slots) == 9
    for i in range(9):
        assert slots[str(i)] is None


@pytest.mark.asyncio
async def test_get_player_state_with_units_and_formation():
    telegram_id = 999888777
    user = {"id": telegram_id, "first_name": "General", "username": "estratega"}
    init_data = _build_init_data(user)

    # 1. Crear jugador y unidades en la base de datos
    unit1_id = uuid.uuid4()
    unit2_id = uuid.uuid4()

    async with async_session() as session:
        player = Player(
            telegram_id=telegram_id,
            first_name="General",
            username="estratega",
        )
        session.add(player)
        await session.flush()

        resource = UserResource(user_id=telegram_id, grain=1200)
        session.add(resource)

        building = UserBuilding(user_id=telegram_id, silo_level=3, galpon_level=2, boyero_level=1)
        session.add(building)

        unit1 = UserUnit(id=unit1_id, user_id=telegram_id, unit_id="U01", level=2)
        unit2 = UserUnit(id=unit2_id, user_id=telegram_id, unit_id="U02", level=1)
        session.add_all([unit1, unit2])
        await session.flush()

        # Asignar unit1 al slot 4 (centro) y dejar unit2 en el banco (sin slot)
        formation = UserFormation(
            user_id=telegram_id,
            slot_4=unit1_id,
        )
        session.add(formation)
        await session.commit()

    # 2. Consultar el estado vía API
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/player/state",
            headers={"X-Telegram-Init-Data": init_data},
        )

    assert response.status_code == 200
    data = response.json()

    # Verificar recursos y edificios persistidos
    assert data["resources"]["grain"] == 1200
    assert data["buildings"]["silo_level"] == 3
    assert data["buildings"]["galpon_level"] == 2
    assert data["buildings"]["boyero_level"] == 1

    # Verificar unidades y sus slots
    units = data["units"]
    assert len(units) == 2

    unit1_data = next((u for u in units if u["id"] == str(unit1_id)), None)
    unit2_data = next((u for u in units if u["id"] == str(unit2_id)), None)

    assert unit1_data is not None
    assert unit1_data["unit_id"] == "U01"
    assert unit1_data["level"] == 2
    assert unit1_data["slot"] == 4  # Desplegada en casilla central

    assert unit2_data is not None
    assert unit2_data["unit_id"] == "U02"
    assert unit2_data["level"] == 1
    assert unit2_data["slot"] is None  # En el banco

    # Verificar mapa de formación
    slots = data["formation"]["slots"]
    assert slots["4"] == str(unit1_id)
    assert slots["0"] is None
    assert slots["8"] is None
