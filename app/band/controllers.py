from dataclasses import asdict
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.auth.services import get_current_user_with_permission
from app.band.models import Band
from app.band.entities import Band as BandEntity
from app.band.services import (
    get_all_bands,
    get_band_by_id,
    get_band_by_gub,
    get_band_by_user,
    get_band_by_name,
    add_new_band,
    make_band,
)
from app.uow import SqlAlchemyUow
from app.user.entities import User
from general_enum.permissions import Permissions
from ports.uow import AbstractUow

router = APIRouter(prefix="/band")


@router.get("/")
async def get_bands(
    current_user: User = Depends(get_current_user_with_permission(Permissions.student)),
    uow: AbstractUow = Depends(SqlAlchemyUow),
) -> List[dict]:

    bands = list(map(asdict, get_all_bands(uow)))
    # band_atual = get_band_by_id(uow, current_user.fk_band)
    aux = []
    for band in bands:
        if current_user.permission > Permissions.table.value:
            aux.append(band)

    return aux


@router.get("/{band_id}")
async def get_band(
    current_user: User = Depends(get_current_user_with_permission(Permissions.student)),
    uow: AbstractUow = Depends(SqlAlchemyUow),
) -> Band:

    if current_user.fk_band is None:
        raise HTTPException(
            status_code=401, detail="You need a band to access this resource"
        )

    band = get_band_by_id(uow, current_user.fk_band)

    if current_user.fk_band != band.id:
        raise HTTPException(
            status_code=401, detail="You are not authorized to access this resource"
        )

    return band


@router.get("/gub/{gub}")
async def get_band(
    gub: int,
    uow: AbstractUow = Depends(SqlAlchemyUow),
    current_user: User = Depends(get_current_user_with_permission(Permissions.student)),
):
    if get_band_by_gub(uow, gub) is None:
        raise HTTPException(
            status_code=404, detail=f"Band with gub '{gub}' does not exist"
        )

    user_band: BandEntity = get_band_by_user(uow, current_user)

    if user_band.gub > gub and current_user.permission < Permissions.table.value:
        raise HTTPException(
            status_code=401,
            detail=f"You are not authorized to access this resource: expected gub less then {gub}, but got {user_band.gub}",
        )

    return asdict(get_band_by_gub(uow, gub))


@router.post("/")
async def add_band(
    band: Band,
    current_user: User = Depends(
        get_current_user_with_permission(Permissions.president)
    ),
    uow: AbstractUow = Depends(SqlAlchemyUow),
) -> None:

    if get_band_by_gub(uow, band.gub) is not None:
        raise HTTPException(
            status_code=400, detail=f"Band with gub '{band.gub}' already exists"
        )

    if get_band_by_name(uow, band.name) is not None:
        raise HTTPException(
            status_code=400, detail=f"Band with name '{band.name}' already exists"
        )

    band.created_for = current_user.username
    band.updated_for = ""
    band = make_band(band)
    add_new_band(uow, band)


# TODO: Create Put method
async def update_band():
    pass


# TODO: Create Delete method
async def delete_band():
    pass
