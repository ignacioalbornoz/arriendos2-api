import requests
from pydantic import NonNegativeFloat
from sqlalchemy.future import select
from shared_models.base import PaymentMixin
from shared_models.transactions import (
    Transaction,
    TransactionWebpay,
    TransactionWebpayMall,
)
from shared_models.tables import Table
from repository.session import SessionDAL
from repository.user_restaurants.user_table_sessions import get_user_table_session
from repository.user_restaurants.restaurants import get_webpay_commerce_code
import os
from fastapi import HTTPException

TRANSBANK_BASE_URL = os.getenv("TRANSBANK_BASE_URL")
RETURN_URL = os.getenv("RETURN_URL")
TRANSBANK_API_WEBPAY_URL = os.getenv("TRANSBANK_API_WEBPAY_URL")
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
COMMERCIAL_CODE = os.getenv("COMMERCIAL_CODE")
MALL_COMMERCIAL_CODE = os.getenv("MALL_COMMERCIAL_CODE")


required_vars = {
    "TRANSBANK_BASE_URL": TRANSBANK_BASE_URL,
    "RETURN_URL": RETURN_URL,
    "TRANSBANK_API_WEBPAY_URL": TRANSBANK_API_WEBPAY_URL,
    "API_SECRET_KEY": API_SECRET_KEY,
    "COMMERCIAL_CODE": COMMERCIAL_CODE,
    "MALL_COMMERCIAL_CODE": MALL_COMMERCIAL_CODE,
}
# Comprobar si alguna de ellas es None
for var_name, var_value in required_vars.items():
    if var_value is None or var_value == "":
        raise EnvironmentError(f"La variable de entorno '{var_name}' no está definida.")

HEADERS = {
    "Tbk-Api-Key-Id": COMMERCIAL_CODE,
    "Tbk-Api-Key-Secret": API_SECRET_KEY,
    "Content-Type": "application/json",
}

HEADERS_MALL = {
    "Tbk-Api-Key-Id": MALL_COMMERCIAL_CODE,
    "Tbk-Api-Key-Secret": API_SECRET_KEY,
    "Content-Type": "application/json",
}


# Este método también permite la creación de una transacción con Transbank, distinguiendo restaurantes que usan el sistema mall o por defecto el de clicomo.
# En mall, corresponde para la compra en múltiples tiendas (restaurantes) en una sola transacción. Y que el usuario pueda pagar en una sola vez.
# También el dinero se distribuye entre los restaurantes correspondientes. El caso de uso más habitual es de un solo restaurante. Pero,
# de esta forma se enviará el dinero al restaurante correspondiente.
# En el formato defecto de clicomo, el cargo se realizará en la cuenta de clicomo, después se debera hacer una transferencia a la cuenta del restaurante.
def create_tbk_transaction(entity_instance: PaymentMixin, session: SessionDAL):
    entity_name = type(entity_instance).get_entity_name()
    user_table_session_instance = get_user_table_session(
        session.user.id, entity_instance.table_id, session
    )

    if user_table_session_instance is None:
        raise HTTPException(
            status_code=400,
            detail="The user does not have an active session, therefore they cannot tip.",
        )

    payload = {
        "buy_order": f"{entity_name}-{entity_instance.id}",
        "session_id": user_table_session_instance.id,
        "return_url": RETURN_URL,
    }

    # Obtiene el commercial_code del restaurante
    commerce_code = get_webpay_commerce_code(
        user_table_session_instance.restaurant_id, session
    )
    restaurant_name = user_table_session_instance.restaurant.name

    post_headers = HEADERS

    if commerce_code:
        payload["details"] = [
            {
                "commerce_code": commerce_code,
                "amount": entity_instance.payment_price,
                "buy_order": f"{restaurant_name}-{entity_name}-{entity_instance.id}",
            }
        ]
        post_headers = HEADERS_MALL
    else:
        payload["amount"] = entity_instance.payment_price
    print(payload, post_headers)
    try:
        table_instance = session.get_by_id(
            select(Table), Table, entity_instance.table_id
        )
        restaurant_id = table_instance.restaurant_id

        response = requests.post(
            TRANSBANK_API_WEBPAY_URL, json=payload, headers=post_headers
        )
        response_data = response.json()
        token = response_data["token"]

        creation_dict = {
            "restaurant_id": restaurant_id,
            "entity_id": entity_instance.id,
            "entity_name": entity_name,
            "payment_method": "webpay",
        }
        transaction_instance = session.create(Transaction, creation_dict)

        if commerce_code:
            creation_dict_metadata = {
                "transaction_id": transaction_instance.id,
                "token_ws": token,
                "commerce_code": commerce_code,
                "buy_order_commerce": f"{restaurant_name}-{entity_name}-{entity_instance.id}",
            }
            session.create(TransactionWebpayMall, creation_dict_metadata)
        else:
            creation_dict_metadata = {
                "transaction_id": transaction_instance.id,
                "token_ws": token,
            }
            session.create(TransactionWebpay, creation_dict_metadata)

    except requests.exceptions.RequestException:
        response_data = {"error_message": "Could not create transaction."}
    return {"request": payload, "response": response_data}


# Permite confirmar una transacción webpay y obtener su resultado final a partir del token_ws.
def commit_tbk_transaction(token_ws: str):
    try:
        response = requests.put(
            f"{TRANSBANK_API_WEBPAY_URL}/{token_ws}", headers=HEADERS
        )
        return response.json()
    except requests.exceptions.RequestException:
        return {"error_message": "Could not commit transaction."}


# Permite confirmar una transacción webpay mall y obtener su resultado final a partir del token_ws.
def commit_tbk_mall_transaction(token_ws: str):
    try:
        response = requests.put(
            f"{TRANSBANK_API_WEBPAY_URL}/{token_ws}", headers=HEADERS_MALL
        )
        return response.json()
    except requests.exceptions.RequestException:
        return {"error_message": "Could not commit transaction."}


# Permite obtener el resultado actual transacción webpay a partir del token_ws.
def get_tbk_transaction(token_ws: str):
    try:
        response = requests.get(
            f"{TRANSBANK_API_WEBPAY_URL}/{token_ws}", headers=HEADERS
        )
        return response.json()
    except requests.exceptions.RequestException:
        return {"error_message": "Could not get transaction."}


# Permite obtener el resultado actual transacción webpay mall a partir del token_ws.
def get_tbk_mall_transaction(token_ws: str):
    try:
        response = requests.get(
            f"{TRANSBANK_API_WEBPAY_URL}/{token_ws}", headers=HEADERS_MALL
        )
        return response.json()
    except requests.exceptions.RequestException:
        return {"error_message": "Could not get transaction."}


# TODO: Sería conveniente pasarle el entity name y entity id en el payload, para así obtener la entidad creada con ese precio
# cambiarle el estado a refund y obtener su amount desde ahí mismo, para que no metan cualquier número.
def refund_tbk_transaction(token_ws: str, amount: NonNegativeFloat):
    payload = {"amount": amount}
    response = requests.post(
        f"{TRANSBANK_API_WEBPAY_URL}/{token_ws}/refunds", json=payload
    )
    response_data = response.json()
    return {"token": token_ws, "amount": amount, "response": response_data}


# Refund de una transacción webpay.
def refund_tbk_instance(transaction_webpay_instance: TransactionWebpay):
    payload = {"amount": transaction_webpay_instance.amount}
    response = requests.post(
        f"{TRANSBANK_API_WEBPAY_URL}/{transaction_webpay_instance.token_ws}/refunds",
        json=payload,
        headers=HEADERS,
    )
    response_data = response.json()
    return {
        "token": transaction_webpay_instance.token_ws,
        "amount": transaction_webpay_instance.amount,
        "response": response_data,
    }


# Refund de una transacción webpay mall.
def refund_tbk_mall_instance(transaction_webpay_instance: TransactionWebpayMall):
    payload = {
        "amount": transaction_webpay_instance.amount,
        "commerce_code": transaction_webpay_instance.commerce_code,
        "buy_order": transaction_webpay_instance.buy_order,
    }
    response = requests.post(
        f"{TRANSBANK_API_WEBPAY_URL}/{transaction_webpay_instance.token_ws}/refunds",
        json=payload,
        headers=HEADERS_MALL,
    )
    response_data = response.json()
    return {
        "token": transaction_webpay_instance.token_ws,
        "amount": transaction_webpay_instance.amount,
        "response": response_data,
    }


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
