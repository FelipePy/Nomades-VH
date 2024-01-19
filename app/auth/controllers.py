from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import JSONResponse

from app.auth.exceptions import InvalidCredentials
from app.auth.schemas import Credentials
from app.auth.services import get_current_user_with_permission
from app.uow import SqlAlchemyUow
from app.user.models import User
from app.utils.controllers.get_controller import get_controller
from general_enum.permissions import Permissions
from ports.uow import AbstractUow
from app.auth import services as sv

router = APIRouter(prefix="/auth")


# use: form_data: OAuth2PasswordRequestForm = Depends(), para testar no docs fastapi
# use: username: str = Body(...),
# use: password: str = Body(...) para sistemas fora do fastapi
@router.post("")
async def login(
        credentials: Credentials,
        uow: AbstractUow = Depends(SqlAlchemyUow)
):
    try:
        token = await sv.add(uow, credentials)

        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={
                "access_token": token.access_token,
                "token_type": "bearer"
            }
        )
    except InvalidCredentials:
        return JSONResponse(status_code=HTTPStatus.UNAUTHORIZED, content={"message": "Credenciais inválidas."})


@router.get("/")
@get_controller(sv)
async def get(
        message_error: str = "Tokens não encontrados.",
        uow: AbstractUow = Depends(SqlAlchemyUow),
        current_user: User = Depends(get_current_user_with_permission(Permissions.root))
):
    ...


@router.post("/logout")
async def logout(token: str = Depends(sv.oauth2_scheme), uow: AbstractUow = Depends(SqlAlchemyUow)):
    response = sv.revoke_token(uow, token)
    if response:
        return response

    return JSONResponse(status_code=HTTPStatus.OK, content={"message": "Logout realizado com sucesso."})


@router.put("/refresh-token")
async def refresh_token(
        current_user: User = Depends(sv.get_current_user),
        uow: AbstractUow = Depends(SqlAlchemyUow)
):
    try:
        token = sv.refresh_token(uow=uow, user=current_user)

        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={
                "access_token": token.access_token,
                "token_type": "bearer"
            }
        )
    except HTTPException as e:
        return e
