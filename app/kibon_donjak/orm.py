from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Table, Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.kibon_donjak.entities import KibonDonjak
from bootstrap.database import mapper_registry
from general_enum.difficulty import Difficulty

kibon_donjak = Table(
    "kibon_donjaks",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("name", String(50), nullable=False, unique=True),
    Column("description", String(255), nullable=False),
    Column("difficulty", Enum(Difficulty), nullable=False),
    Column("created_at", DateTime, default=datetime.now(timezone.utc)),
    Column("updated_at", DateTime, onupdate=datetime.now(timezone.utc)),
)

mapper_registry.map_imperatively(KibonDonjak, kibon_donjak)
