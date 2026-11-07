import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Integer, String, DateTime, func, JSON, Uuid, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    event_name: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Battle(Base):
    """Registro de cada simulación de combate ejecutada por un jugador."""

    __tablename__ = "battles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    wave_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    winner: Mapped[str] = mapped_column(String(16), nullable=False)
    total_ticks: Mapped[int] = mapped_column(Integer, nullable=False)
    player_formation: Mapped[list[Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    replay_log: Mapped[list[Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class UserResource(Base):
    """Recursos económicos acumulados por el jugador."""

    __tablename__ = "user_resources"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("players.telegram_id"),
        primary_key=True,
    )
    grain: Mapped[int] = mapped_column(
        BigInteger,
        default=500,
        server_default="500",
    )
    last_collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class UserBuilding(Base):
    """Niveles de los edificios de la granja del jugador."""

    __tablename__ = "user_buildings"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("players.telegram_id"),
        primary_key=True,
    )
    silo_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
    )
    galpon_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
    )
    boyero_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
    )


class UserUnit(Base):
    """Instancia de una unidad adquirida por el jugador en su banco."""

    __tablename__ = "user_units"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("players.telegram_id"),
        index=True,
        nullable=False,
    )
    unit_id: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )  # ej: "U01"
    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
    )
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class UserFormation(Base):
    """Disposición de unidades en la cuadrícula táctica 3x3 (slots 0 a 8)."""

    __tablename__ = "user_formations"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("players.telegram_id"),
        primary_key=True,
    )
    slot_0: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_units.id"),
        nullable=True,
    )
    slot_1: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_units.id"),
        nullable=True,
    )
    slot_2: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_units.id"),
        nullable=True,
    )
    slot_3: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_units.id"),
        nullable=True,
    )
    slot_4: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_units.id"),
        nullable=True,
    )
    slot_5: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_units.id"),
        nullable=True,
    )
    slot_6: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_units.id"),
        nullable=True,
    )
    slot_7: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_units.id"),
        nullable=True,
    )
    slot_8: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_units.id"),
        nullable=True,
    )

