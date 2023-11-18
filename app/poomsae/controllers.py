from dataclasses import asdict
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.auth.services import get_current_user_with_permission
from app.poomsae import services as poomsae_sv
from app.poomsae.models import Poomsae
from app.uow import SqlAlchemyUow
from app.user.entities import User
from general_enum.permissions import Permissions
from ports.uow import AbstractUow

router = APIRouter(prefix="/poomsae")


# TODO: Create Get Method
@router.get("/")
async def get_all(uow: AbstractUow = Depends(SqlAlchemyUow)) -> List[dict]:
    return list(map(asdict, poomsae_sv.get_all_poomsaes(uow)))


# TODO: Create Get Method
@router.get("/{poomsae_id}")
async def get_poomsae():
    pass


# TODO: Create Post Method
@router.post("/")
async def create_poomsae(
        poomsae: Poomsae,
        uow: AbstractUow = Depends(SqlAlchemyUow),
        current_user: User = Depends(get_current_user_with_permission(Permissions.vice_president))
):
    try:
        poomsae_sv.add(uow, poomsae=poomsae)
        return {"Created": 200}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# TODO: Create Put Method
@router.put("/")
async def update_poomsae():
    pass


# TODO: Create Delete Method
@router.delete("/")
async def delete_poomsae():
    pass
