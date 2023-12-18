import os
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from starlette.status import HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

from app.auth.exceptions import InvalidCredentials
from app.auth.hasher import verify_password
from app.uow import SqlAlchemyUow
from app.user.entities import User
from app.user import services as sv
from general_enum.permissions import Permissions
from ports.uow import AbstractUow
from app.auth.entities import Auth

# TODO: Os métodos fazem as próprias verificações o que resulta em repetição de código,
#  Seria bom já possuir um método que já realizam essas verificações todas

# TODO: Melhorar em todo o sistema as mensagens de erro. Padronizar e criar exceptions personalizadas. ESTÁ HORRÍVEL

# TODO: Fazer um método chamado "auto_revoke_token" para quando o tempo do token se expirar, o sistema automaticamente,
#  invalidar esses tokens

# TODO: Pensar mais sobre os tokens, seu armazenamento e de como realizar a verificação se o usuário realmente está logado
# problemas:
#  - Caso o usuário perca o Token, ele só vai conseguir entrar novamente quando o token dele se expirar sozinho;
#  (da forma que foi implementada, ou seja, só refazer a lógica)

# TODO: Refresh token para que caso o token vença, ele seja inativado

# TODO: Posso pegar o dispositivo que o usuário esta acessando o site, e inserir essa informação no token, para que caso
#  O usuário queira realizar o login em diferentes dispositivos,
#   ele possa (Atualmente o usuário pode ter somente um token)

# TODO: O usuário pode sim possuir vários tokens, para que possa realizar login em diferentes dispositivos.
#  (Ou usar o mesmo)


_ALGORITHM = "HS256"
_TOKEN_EXPIRE_MINUTES = 120
_AUTH_SECRET = os.getenv("AUTH_SECRET")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth")


def _create_token(user_id: UUID) -> str:
    expire = datetime.utcnow() + timedelta(minutes=_TOKEN_EXPIRE_MINUTES)

    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": expire,
        },
        key=_AUTH_SECRET,
        algorithm=_ALGORITHM,
    )


def generate_token(username: str, password: str, uow: AbstractUow) -> Auth:
    user = sv.get_user_by_username(uow, username)
    if not user:
        raise InvalidCredentials()

    if not verify_password(password, user.password):
        raise InvalidCredentials()

    return Auth(
        access_token=_create_token(user.id),
        fk_user=user.id
    )


# TODO: Atualizar para o novo modo com o token sendo inserido no banco de dados
def refresh_token(user: User, uow: AbstractUow, token: str = Depends(oauth2_scheme)) -> Auth:
    with uow:
        auth = uow.auth.get_by_token(token)
        if not is_revoked_token(uow, auth):
            invalidate_token(uow, auth)
            return generate_token(
                username=user.username,
                password=user.password,
                uow=uow
            )
        else:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Token revogado.")


def invalidate_token(uow: AbstractUow, auth: Auth):
    with uow:
        auth.is_invalid = True
        uow.auth.update(auth)


def not_expired_token(token: Auth):
    try:
        payload = jwt.decode(token.access_token, algorithms=_ALGORITHM, key=_AUTH_SECRET)
        expiration = payload.get('exp')

        if expiration is None:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Token inválido")

        return True
    except ExpiredSignatureError:
        HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Token expirado")
    except JWTError:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Token inválido")


def is_revoked_token(uow: AbstractUow, token_db: Auth):
    with uow:
        if not token_db:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Token expirado")

        token_db = uow.auth.get_by_token(token_db.access_token)
        if not token_db:
            return True

        if not not_expired_token(token_db):
            return True

        else:
            return False


def add_token(uow: AbstractUow, username: str, password: str) -> Auth | str:
    with uow:
        # TODO: Tratamento de erros e exceção
        user = sv.get_user_by_username(uow, username)

        if not user:
            raise InvalidCredentials

        token = uow.auth.get_by_user(user.id)

        if not token:
            token = generate_token(username, password, uow)

            uow.auth.add(token)
            return token
        else:
            # TODO: Dessa forma todos os logins terão o mesmo token, se alguem fizer logout, o token será invalidado
            #  em todos os dispositivos.
            if is_revoked_token(uow, token):
                return generate_token(user.username, user.password, uow)

            return token


def revoke_token(uow: AbstractUow, token: str):
    with uow:
        auth = uow.auth.get_by_token(token)
        if not is_revoked_token(uow, auth):
            auth.is_invalid = True
            uow.auth.update(auth)
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Este token já foi revogado.")


# TODO: Atualizar para o novo modo com o token sendo inserido no banco de dados
def get_current_user(
        uow: AbstractUow = Depends(SqlAlchemyUow), token: str = Depends(oauth2_scheme)
) -> User:
    from app.user.services import get_user_by_id
    with uow:
        try:
            auth = uow.auth.get_by_token(token)

            if is_revoked_token(uow, auth):
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Token revogado")

            payload = jwt.decode(auth.access_token, key=_AUTH_SECRET, algorithms=[_ALGORITHM])
            user_id = payload.get("sub")

            if not user_id:
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Token inválido")

            user = get_user_by_id(uow, user_id)
            if user is None:
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Token inválido")

        except JWTError:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Token inválido")

        return user


# TODO: Atualizar para o novo modo com o token sendo inserido no banco de dados
def get_current_user_with_permission(permission: Permissions):
    def _dependency(
            uow: AbstractUow = Depends(SqlAlchemyUow), auth: str = Depends(oauth2_scheme)
    ) -> User:
        user = get_current_user(uow, auth)

        if user.permission < permission.value:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Você não tem autorização para acessar essa página."
            )

        return user

    return _dependency
