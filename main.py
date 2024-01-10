import sys

from app.auth.hasher import hash_password
from loguru import logger
from ports.uow import AbstractUow
from dotenv import load_dotenv
from os import environ
from app.uow import SqlAlchemyUow
from app.user.entities import User
from general_enum.permissions import Permissions
from app.user.services import get_user_by_email


def _load_env():
    load_dotenv(".env")


def _create_tables():
    from bootstrap.database import ensure_all_entities

    ensure_all_entities()


def _create_root(uow: AbstractUow):
    root_user = get_user_by_email(uow, environ.get("ROOT_USER_EMAIL"))

    if not root_user:
        with uow:
            uow.user.add(User(
                username=environ.get("ROOT_USER"),
                email=environ.get("ROOT_USER_EMAIL"),
                password=hash_password(environ.get("ROOT_USER_PASSWORD")),
                permission=Permissions.root,
                fk_band=None
            ))


def _create_student(uow: AbstractUow):
    student_user = get_user_by_email(uow, environ.get("STUDENT_USER_EMAIL"))

    if not student_user:
        with uow:
            uow.user.add(User(
                username=environ.get("STUDENT_USER"),
                email=environ.get("STUDENT_USER_EMAIL"),
                password=hash_password(environ.get("STUDENT_USER_PASSWORD")),
                permission=Permissions.student,
                fk_band=None
            ))


if __name__ == "__main__":
    # TODO: Algumas urls ainda permitem acesso sem o token de acesso

    logger = logger
    logger.remove()
    logger.add(
        sys.stderr,
        format="<blue>{time:YYYY-MM-DD HH:mm:ss}</blue> | <b>{level}</b> | <cyan>{message}</cyan> | "
               "<r>{extra[status_code]}</r> | <b>{extra[user_id]}</b>",
        level='DEBUG'
    )
    logger.add(
        'app.log',
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | "
               "{extra[status_code]} | {extra[user_id]}",
        level='DEBUG'
    )

    _load_env()
    _create_tables()

    uow = SqlAlchemyUow()
    _create_root(uow)
    _create_student(uow)

    import uvicorn

    uvicorn.run(app="bootstrap.server:app", host="0.0.0.0", port=8000)
