from dataclasses import asdict
from functools import wraps
from http import HTTPStatus

from starlette.responses import Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.user.entities import User
from ports.uow import AbstractUow


def get_all_controller(service):
    def inner(func):
        @wraps(func)
        async def wrapper(
                message_error: str,
                uow: AbstractUow,
                current_user: User
        ) -> Response:
            response = await func(message_error, current_user, uow)
            if response:
                return response

            entity = jsonable_encoder(list(map(asdict, service.get(uow))))

            return JSONResponse(
                status_code=HTTPStatus.OK,
                content=entity
            )

        return wrapper

    return inner
