import requests
from shared_models.oneclick_cards import OneClickCard
from shared_models.oneclick_inscriptions import OneClickInscription
from repository.session import SessionDAL
from sqlalchemy import select
import os

ONECLICK_API_SECRET_KEY = os.getenv("ONECLICK_API_SECRET_KEY")
ONECLICK_COMMERCIAL_CODE = os.getenv("ONECLICK_COMMERCIAL_CODE")
ONECLICK_RETURN_URL = os.getenv("ONECLICK_INSCRIPTION_RETURN_URL")
TRANSBANK_API_ONECLICK_INSCRIPTION_URL = os.getenv(
    "TRANSBANK_API_ONECLICK_INSCRIPTION_URL"
)


required_vars = {
    "ONECLICK_API_SECRET_KEY": ONECLICK_API_SECRET_KEY,
    "ONECLICK_COMMERCIAL_CODE": ONECLICK_COMMERCIAL_CODE,
    "ONECLICK_RETURN_URL": ONECLICK_RETURN_URL,
    "TRANSBANK_API_ONECLICK_INSCRIPTION_URL": TRANSBANK_API_ONECLICK_INSCRIPTION_URL,
}
# Comprobar si alguna de ellas es None
for var_name, var_value in required_vars.items():
    if var_value is None or var_value == "":
        raise EnvironmentError(f"La variable de entorno '{var_name}' no está definida.")

HEADERS = {
    "Tbk-Api-Key-Id": ONECLICK_COMMERCIAL_CODE,
    "Tbk-Api-Key-Secret": ONECLICK_API_SECRET_KEY,
    "Content-Type": "application/json",
}


def create_oneclick_inscription(session: SessionDAL):
    # Creando la consulta para seleccionar OneClickCards asociados al usuario de la sesión
    select_query = select(OneClickCard).where(OneClickCard.user_id == session.user.id)

    # Usando SessionDAL para ejecutar la consulta y obtener todos los resultados
    one_click_cards = session.get_all(select_query)

    has_non_null_oneclick_token = any(
        card.oneclick_token is not None for card in one_click_cards
    )

    payload = {
        "username": str(session.user.id),
        "email": str(session.user.email),
        "response_url": ONECLICK_RETURN_URL,
    }

    if has_non_null_oneclick_token:
        response_data = {"error_message": "You already have a credit card on file."}
        return {"request": payload, "response": response_data}

    try:
        response = requests.post(
            TRANSBANK_API_ONECLICK_INSCRIPTION_URL, json=payload, headers=HEADERS
        )
        response_data = response.json()

        token = response_data["token"]

        payload_OneClickCard = {"user_id": session.user.id}

        oneclick_card_instance = session.create(OneClickCard, payload_OneClickCard)
        creation_dict = {
            "oneclick_card_id": oneclick_card_instance.id,
            "token_tbk": token,
        }
        session.create(OneClickInscription, creation_dict)
        # inscription_instance = session.create(OneClickInscription, creation_dict)
        # background_tasks.add_task(
        #     check_oneclick_inscription_timeout,
        #     inscription_instance,
        #     oneclick_card_instance,
        #     session,
        # )
    except requests.exceptions.RequestException:
        response_data = {"error_message": "Could not create OneClick Inscription."}
    return {"request": payload, "response": response_data}


# Permite confirmar una transacción y obtener su resultado final a partir del token_ws.
def commit_oneclick_inscription(token: str):
    try:
        response = requests.put(
            f"{TRANSBANK_API_ONECLICK_INSCRIPTION_URL}/{token}", headers=HEADERS
        )
        return response.json()
    except requests.exceptions.RequestException:
        return {"error_message": "Could not commit inscription."}


# Permite eliminar una inscripción de oneclick
def delete_oneclick_card(
    session: SessionDAL, oneclick_card_instance, hard_delete=False
):
    payload = {
        "tbk_user": oneclick_card_instance.oneclick_token,
        "username": str(session.user.id),
    }

    try:
        response = requests.delete(
            TRANSBANK_API_ONECLICK_INSCRIPTION_URL, json=payload, headers=HEADERS
        )

        if response.status_code == 204:
            session.delete(oneclick_card_instance, hard_delete)
            return {
                "response": response.status_code,
                "error_message": "Could not delete inscription.",
            }
        else:
            return {
                "response": response.status_code,
                "error_message": "Could not delete inscription.",
            }

    except requests.exceptions.RequestException:
        return {"error_message": "Could not delete inscription."}


def create_html_content(msg):
    html_content = f"""
    <html>
        <head>
            <style>
                body, html {{
                    height: 100%;
                    margin: 0;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    background-color: #f0f0f0;
                }}
                #message {{
                    color: #333;
                    font-size: 20px;
                }}
            </style>
        </head>
        <body>
            <div id="message">{msg}</div>
            <script>
                window.onload = function() {{
                    var messageContent = document.getElementById("message").innerText;
                    var dataToSend = JSON.stringify({{action: "next", message: messageContent}});
                    window.ReactNativeWebView.postMessage(dataToSend);
                }}
            </script>
        </body>
    </html>
    """
    return html_content
