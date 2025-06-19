from datetime import datetime, timedelta, timezone
import os
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import PositiveInt
from repository.session import SessionDAL
from fastapi import HTTPException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from sqlalchemy.future import select
from shared_models.user_restaurants.users import User
from repository.exceptions import (
    expired_token_exception,
    invalid_token_exception,
)
from repository.user_restaurants.users import (
    delete_user_data,
    get_supabase_user_by_user_id,
)


# Enviar un correo de confirmación de eliminación de cuenta
def send_delete_user_email(
    user_email: str, delete_user_token: str, apple_instruct: bool = False
) -> None:
    msg = MIMEMultipart("alternative")
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = user_email
    msg["Subject"] = "Confirmación de eliminación de cuenta en Clicomo"
    url = os.getenv("API_CLICOMO_URL")
    text = ""
    html = ""
    if apple_instruct:
        text = f"""
        Hola, 
        Para confirmar la eliminación de tu cuenta, haz clic en el siguiente enlace (Válido por 1 día):
        {url}/confirm-delete-account?token={delete_user_token}
        Si no solicitaste esto, ignora este correo.

        Recuerda que si usaste Apple para registrarte, debes revertir el acceso con apple a la aplicación, con los siguientes pasos:
        1. Abre la aplicación de Configuración en tu iPhone o iPad.
        2. Toca tu nombre en la parte superior de la pantalla para abrir tu cuenta de Apple ID.
        3. Selecciona inicio de sesión y seguridad.
        4. Toca Iniciar sesión con Apple.
        5. Busca clicomo en la lista y selecciona Dejar de usar Apple ID.
        """

        html = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #333;">Confirmación de eliminación de cuenta</h2>
                <p>Hola,</p>
                <p>Para confirmar la eliminación de tu cuenta, por favor haz clic en el botón a continuación:</p>
                <a href="{url}/users/me/confirm?token={delete_user_token}" 
                style="display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">
                Confirmar Eliminación
                </a>

                <p style="margin-top: 20px;">Recuerda que si usaste Apple para registrarte, debes revertir el acceso con apple a la aplicación, con los siguientes pasos:</p>
                <ol>
                    <li>Abre la aplicación de Configuración en tu iPhone o iPad.</li>
                    <li>Toca tu nombre en la parte superior de la pantalla para abrir tu cuenta de Apple ID.</li>
                    <li>Selecciona inicio de sesión y seguridad.</li>
                    <li>Toca Iniciar sesión con Apple.</li>
                    <li>Busca clicomo en la lista y selecciona Dejar de usar Apple ID.</li>
                </ol>

                <p style="margin-top: 20px;">Si no solicitaste esto, simplemente ignora este correo.</p>
                <p>Gracias,</p>
                <p><strong>El equipo de soporte Clicomo</strong></p>
            </div>
        </body>
        </html>
        """

    else:
        text = f"""
        Hola, 
        Para confirmar la eliminación de tu cuenta, haz clic en el siguiente enlace (Válido por 1 día):
        {url}/confirm-delete-account?token={delete_user_token}
        Si no solicitaste esto, ignora este correo.
        """

        html = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #333;">Confirmación de eliminación de cuenta</h2>
                <p>Hola,</p>
                <p>Para confirmar la eliminación de tu cuenta, por favor haz clic en el botón a continuación:</p>
                <a href="{url}/users/me/confirm?token={delete_user_token}" 
                style="display: inline-block; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">
                Confirmar Eliminación
                </a>
                <p style="margin-top: 20px;">Si no solicitaste esto, simplemente ignora este correo.</p>
                <p>Gracias,</p>
                <p><strong>El equipo de soporte Clicomo</strong></p>
            </div>
        </body>
        </html>
        """

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    # Conectar con el servidor SMTP de Brevo
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = os.getenv("SMTP_PORT")
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, user_email, msg.as_string())


# Crea un token que se encarga de eliminar la cuenta de un usuario
def create_delete_user_token(id: PositiveInt) -> str:
    # Crea el delete_user_token
    delete_user_token_expire_hours_int = 24
    to_encode = {
        "sub": str(id),
        "action": "delete_user",
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=delete_user_token_expire_hours_int),
    }
    encoded_jwt = jwt.encode(
        to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )
    return encoded_jwt


# Solicita la eliminación de la cuenta de un usuario
def request_delete_user(session: SessionDAL) -> dict:
    user_instance = session.user
    if not user_instance:
        raise HTTPException(status_code=404, detail="User not found")
    if (
        user_instance.request_delete
        and datetime.now() - user_instance.request_delete < timedelta(days=1)
    ):
        raise HTTPException(status_code=400, detail="Delete request already exists")

    # Consultar si usa apple como provider en supabase
    use_apple = False
    supabase_user = get_supabase_user_by_user_id(user_instance.id, session)
    if supabase_user:
        providers = supabase_user.providers
        if "apple" in providers:
            use_apple = True
    user_email = user_instance.email
    delete_user_token = create_delete_user_token(user_instance.id)
    send_delete_user_email(user_email, delete_user_token, use_apple)
    update_user = {"request_delete": datetime.now(timezone.utc).replace(microsecond=0)}
    session.update(user_instance, update_user)
    if use_apple:
        return {"email": user_email, "detail": "Apple Delete request sent"}
    return {"email": user_email, "detail": "Delete request sent"}


# decodifica el token de eliminación de cuenta
def decode_delete_user_token(delete_user_token: str, session: SessionDAL) -> dict:
    if delete_user_token is None:
        raise invalid_token_exception

    try:
        token = jwt.decode(
            delete_user_token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")],
        )

        action = token.get("action")
        if action is None or action != "delete_user":
            raise invalid_token_exception

        user_id = int(token.get("sub"))
        if user_id is None:
            raise invalid_token_exception

    except ExpiredSignatureError:
        # Token ha expirado
        raise expired_token_exception

    except JWTError:
        raise invalid_token_exception

    user = session.get_by_id(select(User), User, user_id)
    if not user:
        return None
    if not user.request_delete:
        raise HTTPException(status_code=400, detail="Delete request not found")
    if datetime.now() - user.request_delete > timedelta(days=1):
        raise HTTPException(status_code=400, detail="Delete request expired")

    return user


# Elimina la cuenta de un usuario, si el token es válido
def delete_user(delete_user_token: str, session: SessionDAL) -> bool:
    try:
        user_instance = decode_delete_user_token(delete_user_token, session)
        if not user_instance:
            return True
        delete_user_data(user_instance, session)
        return True
    except Exception as e:
        print("Error in delete user", e)
        return False
