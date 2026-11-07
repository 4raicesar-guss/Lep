"""
Tests de integración para el Core Loop Completo (Día 10):
- Merge Tripartito (POST /api/units/merge)
- Recolección Offline (POST /api/resources/collect)
- Inventario de Unidades (GET /api/units/inventory)
- Guardar Formación (POST /api/formation/save)
- Mejora de Edificios (POST /api/buildings/upgrade)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from app.core.config import get_settings
from app.db.base import Base
from app.db.database import async_session, engine
from app.db.models import Player, UserBuilding, UserFormation, UserResource, UserUnit
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

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


# ---------------------------------------------------------------------------
# Tests 1-3, 6-7: Merge Tripartito
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_merge_tripartito_success():
    """1. test_merge_tripartito_success: Crear 3 unidades U01 nivel 1, llamar al endpoint,
    verificar que ahora hay 1 unidad U01 nivel 2 y que los UUIDs viejos desaparecieron."""
    telegram_id = 111111111
    user = {"id": telegram_id, "first_name": "Farmer1"}
    init_data = _build_init_data(user)

    u1_id = uuid.uuid4()
    u2_id = uuid.uuid4()
    u3_id = uuid.uuid4()

    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer1"))
        session.add_all([
            UserUnit(id=u1_id, user_id=telegram_id, unit_id="U01", level=1),
            UserUnit(id=u2_id, user_id=telegram_id, unit_id="U01", level=1),
            UserUnit(id=u3_id, user_id=telegram_id, unit_id="U01", level=1),
        ])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/units/merge",
            headers={"X-Telegram-Init-Data": init_data},
            json={"unit_ids": [str(u1_id), str(u2_id), str(u3_id)]},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["new_level"] == 2
    new_uuid = uuid.UUID(data["new_unit_id"])

    # Verificar estado en base de datos
    async with async_session() as session:
        units_res = await session.execute(
            select(UserUnit).where(UserUnit.user_id == telegram_id)
        )
        units = list(units_res.scalars().all())
        assert len(units) == 1
        assert units[0].id == new_uuid
        assert units[0].unit_id == "U01"
        assert units[0].level == 2

        # Los UUIDs viejos no deben existir
        old_units_res = await session.execute(
            select(UserUnit).where(UserUnit.id.in_([u1_id, u2_id, u3_id]))
        )
        assert len(list(old_units_res.scalars().all())) == 0


@pytest.mark.asyncio
async def test_merge_tripartito_formation_update():
    """2. test_merge_tripartito_formation_update: Equipar las 3 unidades en slot 0, 1 y 2.
    Fusionar. Verificar que slot 0 tiene la nueva unidad y slots 1 y 2 son null."""
    telegram_id = 222222222
    user = {"id": telegram_id, "first_name": "Farmer2"}
    init_data = _build_init_data(user)

    u1_id = uuid.uuid4()
    u2_id = uuid.uuid4()
    u3_id = uuid.uuid4()

    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer2"))
        session.add_all([
            UserUnit(id=u1_id, user_id=telegram_id, unit_id="U01", level=1),
            UserUnit(id=u2_id, user_id=telegram_id, unit_id="U01", level=1),
            UserUnit(id=u3_id, user_id=telegram_id, unit_id="U01", level=1),
        ])
        await session.flush()

        formation = UserFormation(
            user_id=telegram_id,
            slot_0=u1_id,
            slot_1=u2_id,
            slot_2=u3_id,
        )
        session.add(formation)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/units/merge",
            headers={"X-Telegram-Init-Data": init_data},
            json={"unit_ids": [str(u1_id), str(u2_id), str(u3_id)]},
        )

    assert response.status_code == 200
    data = response.json()
    new_uuid = uuid.UUID(data["new_unit_id"])

    # Verificar formación
    async with async_session() as session:
        formation = await session.scalar(
            select(UserFormation).where(UserFormation.user_id == telegram_id)
        )
        assert formation is not None
        assert formation.slot_0 == new_uuid
        assert formation.slot_1 is None
        assert formation.slot_2 is None


@pytest.mark.asyncio
async def test_merge_tripartito_fails_mixed_levels():
    """3. test_merge_tripartito_fails_mixed_levels: Intentar fusionar dos nivel 1 y una nivel 2.
    Debe fallar con 400."""
    telegram_id = 333333333
    user = {"id": telegram_id, "first_name": "Farmer3"}
    init_data = _build_init_data(user)

    u1_id = uuid.uuid4()
    u2_id = uuid.uuid4()
    u3_id = uuid.uuid4()

    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer3"))
        session.add_all([
            UserUnit(id=u1_id, user_id=telegram_id, unit_id="U01", level=1),
            UserUnit(id=u2_id, user_id=telegram_id, unit_id="U01", level=1),
            UserUnit(id=u3_id, user_id=telegram_id, unit_id="U01", level=2),  # Nivel diferente
        ])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/units/merge",
            headers={"X-Telegram-Init-Data": init_data},
            json={"unit_ids": [str(u1_id), str(u2_id), str(u3_id)]},
        )

    assert response.status_code == 400

    # Las 3 unidades deben seguir existiendo intactas
    async with async_session() as session:
        units_res = await session.execute(
            select(UserUnit).where(UserUnit.user_id == telegram_id)
        )
        assert len(list(units_res.scalars().all())) == 3


@pytest.mark.asyncio
async def test_merge_tripartito_fails_different_units():
    """6. test_merge_tripartito_fails_different_units: Intentar fusionar tipos distintos (U01 y U02).
    Debe fallar con 400."""
    telegram_id = 333333334
    user = {"id": telegram_id, "first_name": "Farmer3b"}
    init_data = _build_init_data(user)

    u1_id = uuid.uuid4()
    u2_id = uuid.uuid4()
    u3_id = uuid.uuid4()

    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer3b"))
        session.add_all([
            UserUnit(id=u1_id, user_id=telegram_id, unit_id="U01", level=1),
            UserUnit(id=u2_id, user_id=telegram_id, unit_id="U01", level=1),
            UserUnit(id=u3_id, user_id=telegram_id, unit_id="U02", level=1),  # Tipo diferente
        ])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/units/merge",
            headers={"X-Telegram-Init-Data": init_data},
            json={"unit_ids": [str(u1_id), str(u2_id), str(u3_id)]},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_merge_tripartito_fails_level_3():
    """7. test_merge_tripartito_fails_level_3: Intentar fusionar unidades que ya son nivel 3.
    Debe fallar con 400."""
    telegram_id = 333333335
    user = {"id": telegram_id, "first_name": "Farmer3c"}
    init_data = _build_init_data(user)

    u1_id = uuid.uuid4()
    u2_id = uuid.uuid4()
    u3_id = uuid.uuid4()

    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer3c"))
        session.add_all([
            UserUnit(id=u1_id, user_id=telegram_id, unit_id="U01", level=3),
            UserUnit(id=u2_id, user_id=telegram_id, unit_id="U01", level=3),
            UserUnit(id=u3_id, user_id=telegram_id, unit_id="U01", level=3),
        ])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/units/merge",
            headers={"X-Telegram-Init-Data": init_data},
            json={"unit_ids": [str(u1_id), str(u2_id), str(u3_id)]},
        )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Tests 4-5: Recolección Offline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_collect_offline_with_cap():
    """4. test_collect_offline_with_cap: Simular un usuario con last_collected_at hace 20 horas,
    silo nivel 1 (cap 6h). Verificar que solo gana 6h de producción y el flag hours_capped es true."""
    telegram_id = 444444444
    user = {"id": telegram_id, "first_name": "Farmer4"}
    init_data = _build_init_data(user)

    twenty_hours_ago = datetime.now(UTC) - timedelta(hours=20)

    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer4"))
        session.add(UserResource(user_id=telegram_id, grain=500, last_collected_at=twenty_hours_ago))
        session.add(UserBuilding(user_id=telegram_id, silo_level=1, galpon_level=1, boyero_level=1))
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/resources/collect",
            headers={"X-Telegram-Init-Data": init_data},
        )

    assert response.status_code == 200
    data = response.json()

    # Rate: 120 * (1 + 0.15 * 1) = 138 grano/hora
    # Cap para Silo nivel 1: 4 + 2 * 1 = 6 horas
    # Producción esperada: 6 * 138 = 828 grano
    assert data["hours_capped"] is True
    assert data["grain_collected"] == 828
    assert data["new_total_grain"] == 500 + 828

    # Verificar en base de datos
    async with async_session() as session:
        res = await session.scalar(
            select(UserResource).where(UserResource.user_id == telegram_id)
        )
        assert res.grain == 1328


@pytest.mark.asyncio
async def test_collect_offline_uncapped():
    """5. test_collect_offline_uncapped: Simular 2 horas (< cap 6h) y galpon nivel 1.
    Verificar que hours_capped es false y la cantidad de grano es proporcional."""
    telegram_id = 555555555
    user = {"id": telegram_id, "first_name": "Farmer5"}
    init_data = _build_init_data(user)

    two_hours_ago = datetime.now(UTC) - timedelta(hours=2)

    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer5"))
        session.add(UserResource(user_id=telegram_id, grain=500, last_collected_at=two_hours_ago))
        session.add(UserBuilding(user_id=telegram_id, silo_level=1, galpon_level=1, boyero_level=1))
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/resources/collect",
            headers={"X-Telegram-Init-Data": init_data},
        )

    assert response.status_code == 200
    data = response.json()

    # Rate: 138 grano/h * 2h = 276 grano
    assert data["hours_capped"] is False
    assert data["grain_collected"] == 276
    assert data["new_total_grain"] == 500 + 276


# ---------------------------------------------------------------------------
# Test 8: Inventario de Unidades
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_inventory_returns_all_units():
    """8. test_get_inventory_returns_all_units: Devuelve lista de unidades con su slot correspondiente."""
    telegram_id = 666666666
    user = {"id": telegram_id, "first_name": "Farmer6"}
    init_data = _build_init_data(user)

    u1_id = uuid.uuid4()
    u2_id = uuid.uuid4()

    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer6"))
        session.add_all([
            UserUnit(id=u1_id, user_id=telegram_id, unit_id="U01", level=1),
            UserUnit(id=u2_id, user_id=telegram_id, unit_id="U02", level=2),
        ])
        await session.flush()
        # u1 desplegada en slot 4, u2 en reserva
        session.add(UserFormation(user_id=telegram_id, slot_4=u1_id))
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/units/inventory",
            headers={"X-Telegram-Init-Data": init_data},
        )

    assert response.status_code == 200
    units = response.json()
    assert len(units) == 2

    item1 = next((u for u in units if u["id"] == str(u1_id)), None)
    item2 = next((u for u in units if u["id"] == str(u2_id)), None)

    assert item1 is not None
    assert item1["unit_id"] == "U01"
    assert item1["level"] == 1
    assert item1["slot"] == 4

    assert item2 is not None
    assert item2["unit_id"] == "U02"
    assert item2["level"] == 2
    assert item2["slot"] is None


# ---------------------------------------------------------------------------
# Tests 9-10: Guardar Formación
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_formation_valid():
    """9. test_save_formation_valid: Guardar formación válida con slots 0 y 4 ocupados."""
    telegram_id = 777777777
    user = {"id": telegram_id, "first_name": "Farmer7"}
    init_data = _build_init_data(user)

    u1_id = uuid.uuid4()
    u2_id = uuid.uuid4()

    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer7"))
        session.add_all([
            UserUnit(id=u1_id, user_id=telegram_id, unit_id="U01", level=1),
            UserUnit(id=u2_id, user_id=telegram_id, unit_id="U03", level=1),
        ])
        await session.commit()

    payload = {
        "slots": {
            "0": str(u1_id),
            "1": None,
            "2": None,
            "3": None,
            "4": str(u2_id),
            "5": None,
            "6": None,
            "7": None,
            "8": None,
        }
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/formation/save",
            headers={"X-Telegram-Init-Data": init_data},
            json=payload,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["slots"]["0"] == str(u1_id)
    assert data["slots"]["4"] == str(u2_id)
    assert data["slots"]["1"] is None

    # Verificar en base de datos
    async with async_session() as session:
        formation = await session.scalar(
            select(UserFormation).where(UserFormation.user_id == telegram_id)
        )
        assert formation is not None
        assert formation.slot_0 == u1_id
        assert formation.slot_4 == u2_id
        assert formation.slot_1 is None


@pytest.mark.asyncio
async def test_save_formation_duplicate_uuid_fails():
    """10. test_save_formation_duplicate_uuid_fails: Intentar colocar la misma unidad en dos slots."""
    telegram_id = 888888888
    user = {"id": telegram_id, "first_name": "Farmer8"}
    init_data = _build_init_data(user)

    u1_id = uuid.uuid4()

    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer8"))
        session.add(UserUnit(id=u1_id, user_id=telegram_id, unit_id="U01", level=1))
        await session.commit()

    payload = {
        "slots": {
            "0": str(u1_id),
            "1": str(u1_id),  # Duplicado
            "2": None,
        }
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/formation/save",
            headers={"X-Telegram-Init-Data": init_data},
            json=payload,
        )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Tests 11-12: Mejora de Edificios
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upgrade_building_success():
    """11. test_upgrade_building_success: Mejorar edificio silo con grano suficiente."""
    telegram_id = 999999999
    user = {"id": telegram_id, "first_name": "Farmer9"}
    init_data = _build_init_data(user)

    # Coste nivel 1: 100 * (1.5 ^ 1) = 150 grano
    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer9"))
        session.add(UserResource(user_id=telegram_id, grain=1000))
        session.add(UserBuilding(user_id=telegram_id, silo_level=1, galpon_level=1, boyero_level=1))
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/buildings/upgrade",
            headers={"X-Telegram-Init-Data": init_data},
            json={"building_id": "silo"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["building_id"] == "silo"
    assert data["new_level"] == 2
    assert data["cost"] == 150
    assert data["remaining_grain"] == 850

    # Verificar en base de datos
    async with async_session() as session:
        building = await session.scalar(
            select(UserBuilding).where(UserBuilding.user_id == telegram_id)
        )
        assert building.silo_level == 2

        resource = await session.scalar(
            select(UserResource).where(UserResource.user_id == telegram_id)
        )
        assert resource.grain == 850


@pytest.mark.asyncio
async def test_upgrade_building_insufficient_grain_fails():
    """12. test_upgrade_building_insufficient_grain_fails: Rechazar si el grano no alcanza."""
    telegram_id = 101010101
    user = {"id": telegram_id, "first_name": "Farmer10"}
    init_data = _build_init_data(user)

    # Solo 50 de grano (se requieren 150)
    async with async_session() as session:
        session.add(Player(telegram_id=telegram_id, first_name="Farmer10"))
        session.add(UserResource(user_id=telegram_id, grain=50))
        session.add(UserBuilding(user_id=telegram_id, silo_level=1, galpon_level=1, boyero_level=1))
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/buildings/upgrade",
            headers={"X-Telegram-Init-Data": init_data},
            json={"building_id": "galpon"},
        )

    assert response.status_code == 400

    # Verificar que no cambió nada
    async with async_session() as session:
        building = await session.scalar(
            select(UserBuilding).where(UserBuilding.user_id == telegram_id)
        )
        assert building.galpon_level == 1

        resource = await session.scalar(
            select(UserResource).where(UserResource.user_id == telegram_id)
        )
        assert resource.grain == 50
