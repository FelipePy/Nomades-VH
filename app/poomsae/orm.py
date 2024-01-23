from datetime import datetime, timezone
from sqlalchemy import Enum
from uuid import uuid4

from sqlalchemy import Table, Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.poomsae.entities import Poomsae
from bootstrap.database import mapper_registry
from general_enum.difficulty import Difficulty

poomsaes = Table(
    "poomsaes",
    mapper_registry.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid4),
    Column("name", String[50], nullable=False, unique=True),
    Column("description", String[250], nullable=False),
    Column("difficulty", Enum(Difficulty), nullable=False),
    Column("fk_band", UUID(as_uuid=True), ForeignKey("bands.id", ondelete='SET NULL'), nullable=True),
    Column("created_for", UUID(as_uuid=True), nullable=False),
    Column("updated_for", UUID(as_uuid=True), nullable=False),
    Column("created_at", DateTime, default=datetime.now(timezone.utc)),
    Column("updated_at", DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)),
)

mapper_registry.map_imperatively(Poomsae, poomsaes)
