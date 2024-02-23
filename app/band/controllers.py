from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.responses import Response
from starlette.responses import JSONResponse

from app.auth.services import get_current_user_with_permission
from app.band.models import Band
from app.uow import SqlAlchemyUow
from app.user.entities import User
from app.utils.controllers.create_controller import create_controller
from app.utils.controllers.delete_controller import delete_controller
from app.utils.controllers.get_by_controller import get_by_controller
from app.utils.controllers.get_controller import get_controller
from app.utils.controllers.update_controller import update_controller
from general_enum.permissions import Permissions
from ports.uow import AbstractUow
from app.band import services as sv

router = APIRouter(prefix="/band")

# TODO: Arrumar essas verificações, está muito amador


@router.get("/")
@get_controller(sv)
async def get(
        message_error: str = "Não foram encontradas faixas.",
        current_user: User = Depends(get_current_user_with_permission(Permissions.student)),
        uow: AbstractUow = Depends(SqlAlchemyUow),
) -> Response:
    if current_user.permission.value < Permissions.table.value:
        band = sv.get_by_user(uow, current_user)
        if band:
            return JSONResponse(
                status_code=HTTPStatus.OK,
                content=jsonable_encoder(sv.get_minors_band(uow, band.gub))
            )

        return JSONResponse(
            status_code=HTTPStatus.FORBIDDEN,
            content={"message": "Você não possui uma faixa. Procure mais informações com seu professor."}
        )


@router.get("/me")
async def get_my_band(
        current_user: User = Depends(get_current_user_with_permission(Permissions.student)),
        uow: AbstractUow = Depends(SqlAlchemyUow),
):
    if current_user.fk_band is None:
        return JSONResponse(
            status_code=HTTPStatus.FORBIDDEN,
            content={"message": "Você não possui uma faixa. Converse com seu professor para mais detalhes."}
        )

    band = sv.get_by_user(uow, current_user)

    return band


@router.get("/{param}")
@get_by_controller(sv.get_by_id)
async def get_by_id(
        param: UUID,
        message_error: str = "Faixa não encontrada.",
        uow: AbstractUow = Depends(SqlAlchemyUow),
        current_user: User = Depends(get_current_user_with_permission(Permissions.student))
) -> Response:
    band = sv.get_by_id(uow, param)
    band_user = sv.get_by_user(uow, current_user)

    if band_user is None and current_user.permission.value < Permissions.table.value:
        return JSONResponse(
            status_code=HTTPStatus.FORBIDDEN,
            content={"message": "Você não possui uma faixa! Converse com seu professor para mais detalhes."}
        )

    if band and band_user and band_user.gub > band.gub and current_user.permission.value < Permissions.table.value:
        return JSONResponse(
            status_code=HTTPStatus.FORBIDDEN,
            content={"message": "Você ainda não chegou nessa faixa."}
        )


@router.get("/gub/{param}")
@get_by_controller(sv.get_by_gub)
async def get_by_gub(
        param: int,
        message_error: str = "Faixa não encontrada.",
        uow: AbstractUow = Depends(SqlAlchemyUow),
        current_user: User = Depends(get_current_user_with_permission(Permissions.student)),
) -> Response:
    band = sv.get_by_user(uow, current_user)

    if band and current_user.permission.value < Permissions.table.value and band.gub > param:
        return JSONResponse(
            status_code=HTTPStatus.FORBIDDEN,
            content={
                "message": "Você ainda não chegou nessa faixa."
            }
        )


@router.post("/")
@create_controller(sv)
async def post(
        model: Band,
        message_success: str = "Faixa criada com sucesso.",
        message_error: str = "Erro ao criar a faixa.",
        uow: AbstractUow = Depends(SqlAlchemyUow),
        current_user: User = Depends(
            get_current_user_with_permission(Permissions.table)
        )
) -> Response:
    if sv.get_by_gub(uow, model.gub) is not None:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={"message": f"Gub {model.gub} já existe."}
        )


@router.put("/{uuid}")
@update_controller(sv)
async def put(
        uuid: UUID,
        model: Band,
        message_success: str = "Faixa atualizada.",
        message_error: str = "Faixa não atualizada.",
        uow: AbstractUow = Depends(SqlAlchemyUow),
        current_user: User = Depends(
            get_current_user_with_permission(Permissions.table)
        )
):
    ...


@router.delete("/{uuid}")
@delete_controller(sv)
async def delete(
        uuid: UUID,
        message_success: str = "Faixa deletada.",
        message_error: str = "Faixa não encontrada.",
        uow: AbstractUow = Depends(SqlAlchemyUow),
        current_user: User = Depends(get_current_user_with_permission(Permissions.table))
) -> Response:
    ...
