from datetime import datetime, timedelta, timezone
import os
from jose import jwt
from pydantic import PositiveInt
from sqlalchemy.future import select
from shared_models.entity import Entity
from shared_models.entity_permission import EntityPermission
from shared_models.user_restaurants.user_tokens import RefreshToken
from repository.session import SessionDAL
from fastapi import HTTPException
from shared_models.user_restaurants.users import User, SupabaseUser
from repository.user_restaurants.users import (
    get_user_by_email,
    get_user_by_supabase_id,
    get_supabase_user_by_user_id,
)
import uuid


def create_token_session_id():
    return str(uuid.uuid4())


# Crea un access_token codificado en jwt a partir del id del User con un tiempo de expiración de 60 días.
def create_access_token(id: PositiveInt, token_session_id: str, session: SessionDAL):
    # Verificar si existe un token de sesión activo
    token_query = select(RefreshToken).where(
        RefreshToken.user_id == id, RefreshToken.session_id == token_session_id
    )
    token_instance = session.get(token_query)

    # Si no existe, crea un nuevo token de sesión
    if not token_instance:
        token_instance = session.create(
            RefreshToken,
            {
                "session_id": token_session_id,
                "user_id": id,
            },
        )

    # Crea el access_token
    ACCESS_TOKEN_EXPIRE_HOURS = os.getenv("ACCESS_TOKEN_EXPIRE_HOURS")
    access_token_expire_hours_int = int(ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": str(id),
        "session_id": token_session_id,
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=access_token_expire_hours_int),
    }
    encoded_jwt = jwt.encode(
        to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )
    return encoded_jwt, token_instance


# Crea un refresh_token codificado en jwt a partir del id del User con un tiempo de expiración más largo.
def create_refresh_token(
    id: PositiveInt, token_instance, token_session_id: str, session: SessionDAL
):
    REFRESH_TOKEN_EXPIRE_HOURS = os.getenv("REFRESH_TOKEN_EXPIRE_HOURS")
    refresh_token_expire_hours_int = int(REFRESH_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": str(id),
        "session_id": token_session_id,
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=refresh_token_expire_hours_int),
    }
    encoded_jwt = jwt.encode(
        to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )

    # Guardar el refresh token en la base de datos
    session.update(
        token_instance,
        {
            "refresh_token_id": encoded_jwt,
        },
    )

    return encoded_jwt


# Obtiene los EntityPermission de una session sobre una determinada Entity.
def get_permissions(entity_name: str, session: SessionDAL):
    entity_query = select(Entity).where(Entity.name == entity_name)
    entity = session.get(entity_query)
    if not entity:
        return
    permission_query = (
        select(EntityPermission)
        .where(EntityPermission.role == session.role)
        .where(EntityPermission.entity_id == entity.id)
    )
    permissions = session.get(permission_query)
    return permissions


def get_user_by_supabase(supabase_user_data, session: SessionDAL):
    user_instance = get_user_by_supabase_id(str(supabase_user_data.user.id), session)
    user_instance_without_supabase = get_user_by_email(
        supabase_user_data.user.email, session
    )
    # print(supabase_user_data)

    if not user_instance:
        if user_instance_without_supabase:
            session.create(
                SupabaseUser,
                {
                    "id": supabase_user_data.user.id,
                    "user_id": user_instance_without_supabase.id,
                    "email": supabase_user_data.user.email,
                    "aud": supabase_user_data.user.aud,
                    "created_at": supabase_user_data.user.created_at.replace(
                        microsecond=0, tzinfo=timezone.utc
                    ),
                    "confirmed_at": supabase_user_data.user.confirmed_at.replace(
                        microsecond=0, tzinfo=timezone.utc
                    )
                    if supabase_user_data.user.confirmed_at
                    else None,
                    "email_confirmed_at": supabase_user_data.user.email_confirmed_at.replace(
                        microsecond=0, tzinfo=timezone.utc
                    )
                    if supabase_user_data.user.email_confirmed_at
                    else None,
                    "last_sign_in_at": supabase_user_data.user.last_sign_in_at.replace(
                        microsecond=0, tzinfo=timezone.utc
                    )
                    if supabase_user_data.user.last_sign_in_at
                    else None,
                    "updated_at": supabase_user_data.user.updated_at.replace(
                        microsecond=0, tzinfo=timezone.utc
                    )
                    if supabase_user_data.user.updated_at
                    else None,
                    "is_anonymous": supabase_user_data.user.is_anonymous,
                    "providers": supabase_user_data.user.app_metadata["providers"]
                    if supabase_user_data.user.app_metadata
                    else None,
                },
            )
            user_instance = user_instance_without_supabase
        else:
            # Crear usuario, toma la primera parte del email como display_name
            display_name = supabase_user_data.user.email.split("@")[0]
            user_instance = session.create(
                User,
                {
                    "display_name": display_name,
                    "email": supabase_user_data.user.email,
                },
            )
            session.create(
                SupabaseUser,
                {
                    "id": supabase_user_data.user.id,
                    "user_id": user_instance.id,
                    "email": supabase_user_data.user.email,
                    "aud": supabase_user_data.user.aud,
                    "created_at": supabase_user_data.user.created_at.replace(
                        microsecond=0, tzinfo=timezone.utc
                    ),
                    "confirmed_at": supabase_user_data.user.confirmed_at.replace(
                        microsecond=0, tzinfo=timezone.utc
                    )
                    if supabase_user_data.user.confirmed_at
                    else None,
                    "email_confirmed_at": supabase_user_data.user.email_confirmed_at.replace(
                        microsecond=0, tzinfo=timezone.utc
                    )
                    if supabase_user_data.user.email_confirmed_at
                    else None,
                    "last_sign_in_at": supabase_user_data.user.last_sign_in_at.replace(
                        microsecond=0, tzinfo=timezone.utc
                    )
                    if supabase_user_data.user.last_sign_in_at
                    else None,
                    "updated_at": supabase_user_data.user.updated_at.replace(
                        microsecond=0, tzinfo=timezone.utc
                    )
                    if supabase_user_data.user.updated_at
                    else None,
                    "is_anonymous": supabase_user_data.user.is_anonymous,
                    "providers": supabase_user_data.user.app_metadata["providers"]
                    if supabase_user_data.user.app_metadata
                    else None,
                },
            )
    else:
        # Actualizar datos de usuario
        supabase_user_instance = get_supabase_user_by_user_id(user_instance.id, session)
        session.update(
            supabase_user_instance,
            {
                "email": supabase_user_data.user.email,
                "confirmed_at": supabase_user_data.user.confirmed_at
                if supabase_user_data.user.confirmed_at
                else None,
                "email_confirmed_at": supabase_user_data.user.email_confirmed_at
                if supabase_user_data.user.email_confirmed_at
                else None,
                "last_sign_in_at": supabase_user_data.user.last_sign_in_at
                if supabase_user_data.user.last_sign_in_at
                else None,
                "updated_at": supabase_user_data.user.updated_at
                if supabase_user_data.user.updated_at
                else None,
                "providers": supabase_user_data.user.app_metadata["providers"]
                if supabase_user_data.user.app_metadata
                else None,
            },
        )

    token_session_id = create_token_session_id()
    access_token, token_instance = create_access_token(
        user_instance.id, token_session_id, session
    )
    refresh_token = create_refresh_token(
        user_instance.id, token_instance, token_session_id, session
    )

    # supabase_user_instance = get_supabase_user_by_user_id(user_instance.id, session)

    if supabase_user_data.user.email_confirmed_at:
        verified_email = True
    else:
        verified_email = False
        raise HTTPException(status_code=403, detail="Email not confirmed")

    if user_instance.terms_accepted:
        terms_acepted = True
    else:
        terms_acepted = False
    return {
        "token": access_token,
        "refresh_token": refresh_token,
        "user": user_instance,
        "terms_accepted": terms_acepted,
        "verified_email": verified_email,
    }


def clear_user_tokens_by_user_id(user_id: PositiveInt, session: SessionDAL):
    token_query = select(RefreshToken).where(RefreshToken.user_id == user_id)
    token_instance = session.get_all(token_query)
    for token in token_instance:
        session.delete(token, True, commit=False)
    session.commit()
    return True


def clear_user_token_by_session_id(session_id: str, session: SessionDAL):
    token_query = select(RefreshToken).where(RefreshToken.session_id == session_id)
    token_instance = session.get(token_query)
    session.delete(token_instance, True)
    return True


def get_token_session_by_id(session_id: str, session: SessionDAL):
    token_query = select(RefreshToken).where(RefreshToken.session_id == session_id)
    token_instance = session.get(token_query)
    return token_instance
