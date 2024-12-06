from typing import List
from uuid import UUID as PyUUID

from sqlalchemy import UUID as SQLUUID
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import Mapped, relationship

from ports.entity import Entity


class Poomsae(Entity):
    __tablename__ = 'poomsaes'
    name: Mapped[str] = Column(String(50), unique=True, nullable=False)
    description: Mapped[str] = Column(String(600), nullable=False)

    bands: Mapped['Band'] = relationship(
        secondary='band_poomsae', back_populates='poomsaes'
    )


class BandPoomsae(Entity):
    __tablename__ = 'band_poomsae'

    band_id: PyUUID = Column(
        SQLUUID(as_uuid=True),
        ForeignKey('bands.id', ondelete='CASCADE'),
        primary_key=True,
    )
    poomsae_id: PyUUID = Column(
        SQLUUID(as_uuid=True),
        ForeignKey('poomsaes.id', ondelete='CASCADE'),
        primary_key=True,
    )
