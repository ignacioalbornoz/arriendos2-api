import requests
from shared_models.base import PaymentMixin
from shared_models.transactions import Transaction, TransactionOneclick
from shared_models.tables import Table
from repository.session import SessionDAL
from sqlalchemy.future import select
import os
from repository.transbank_webpay_transactions_local import (
    get_consumables_by_order_id,
    get_next_runner_for_table,
    approve_transaction_entity,
    activate_user_table_session,
    update_consumables_to_en_fila,
    restore_transaction_validation,
)
from repository.exceptions import request_exception, TransactionTransbankException
from fastapi.responses import HTMLResponse
from repository.oneclick_cards import get_oneclick_card
from repository.user_restaurants.user_table_sessions import get_user_table_session
from repository.user_restaurants.restaurants import get_oneclick_commerce_code
from fastapi import HTTPException


TRANSBANK_API_ONECLICK_TRANSACTION_URL = os.getenv(
    "TRANSBANK_API_ONECLICK_TRANSACTION_URL"
)

ONECLICK_API_SECRET_KEY = os.getenv("ONECLICK_API_SECRET_KEY")
ONECLICK_COMMERCIAL_CODE = os.getenv("ONECLICK_COMMERCIAL_CODE")

ONECLICK_TRANSACTION_COMMERCIAL_CODE = os.getenv("ONECLICK_TRANSACTION_COMMERCIAL_CODE")

required_vars = {
    "TRANSBANK_API_ONECLICK_TRANSACTION_URL": TRANSBANK_API_ONECLICK_TRANSACTION_URL,
    "ONECLICK_API_SECRET_KEY": ONECLICK_API_SECRET_KEY,
    "ONECLICK_COMMERCIAL_CODE": ONECLICK_COMMERCIAL_CODE,
    "ONECLICK_TRANSACTION_COMMERCIAL_CODE": ONECLICK_TRANSACTION_COMMERCIAL_CODE,
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


# Permite crear una URL de transacción con Transbank Oneclick. Al crear una URL de transacción, se permite "comprar"
# una entidad en la base de datos que herede de PaymentMixin (e.g. Order). Luego, se genera esta URL de transacción,
# pasando la información de la entidad en el payload. Cuando el usuario complete la transacción exitosamente,
# se actualizará el campo 'payment_status' a 'pagado'.
def create_oneclick_transaction(
    entity_instance: PaymentMixin, session: SessionDAL, installments_number: int
):
    entity_name = type(entity_instance).get_entity_name()
    user_table_session_instance = get_user_table_session(
        session.user.id, entity_instance.table_id, session
    )
    if user_table_session_instance is None:
        raise HTTPException(
            status_code=400,
            detail="The user does not have an active session, therefore they cannot tip.",
        )

    # Obtiene el commercial_code del restaurante
    commerce_code = get_oneclick_commerce_code(
        user_table_session_instance.restaurant_id, session
    )
    restaurant_name = user_table_session_instance.restaurant.name

    # Se obtiene la tarjeta oneclick del usuario
    oneclick_card_instance = get_oneclick_card(session)[0]
    payload = {
        "username": str(session.user.id),
        "tbk_user": str(oneclick_card_instance.oneclick_token),
        "buy_order": f"{entity_name}-{entity_instance.id}",
        "details": [
            {
                "commerce_code": commerce_code
                if commerce_code
                else ONECLICK_TRANSACTION_COMMERCIAL_CODE,
                "buy_order": f"{restaurant_name}-{entity_name}-{entity_instance.id}"
                if commerce_code
                else f"{entity_name}-{entity_instance.id}",
                "amount": entity_instance.payment_price,
                "installments_number": installments_number,
            }
        ],
    }
    # Se prepara la transacción en la base de datos, se obtiene todos los datos necesarios para la transacción.
    try:
        table_instance = session.get_by_id(
            select(Table), Table, entity_instance.table_id
        )
        restaurant_id = table_instance.restaurant_id
        creation_dict = {
            "restaurant_id": restaurant_id,
            "entity_id": entity_instance.id,
            "entity_name": entity_name,
            "installments_number": installments_number,
            "payment_method": "oneclick",
        }
        transaction_instance = session.create(Transaction, creation_dict)
        # Se obtienen los consumables de la orden
        if entity_name == "order":
            runner_instance = get_next_runner_for_table(
                user_table_session_instance, session
            )
            consumable_history_instances = get_consumables_by_order_id(
                entity_instance.id, session
            )
    except Exception as e:
        print("Error en la transacción", e)
        raise request_exception(
            detail="ERROR SERVIDOR",
            status_code=502,
        )

    # Preprocesamos la transacción, suponiendo que no hay errores y que se concretará.
    correct_transaction = False
    paid = False
    progress = 0
    entity_table_session = None
    runner_table_session_instance = None
    details = None
    try:
        # Se marca la transacción con un status done=True.
        session.update(transaction_instance, {"done": True})
        progress = 1
        # Se aprueba la entidad
        entity_table_session = approve_transaction_entity(
            entity_name,
            entity_instance,
            user_table_session_instance.id,
            session,
        )
        progress = 2

        # Si la entidad es una orden, se actualizan los consumibles a "en fila"
        if entity_name == "order":
            update_consumables_to_en_fila(consumable_history_instances, session)
            progress = 3

            # Se activa la sesión de la mesa si es la primera compra
            if user_table_session_instance and runner_instance:
                runner_table_session_instance = activate_user_table_session(
                    user_table_session_instance, runner_instance, session
                )
                progress = 4
        # Confirmar la transacción en Transbank
        paid = True
        response = requests.post(
            TRANSBANK_API_ONECLICK_TRANSACTION_URL, json=payload, headers=HEADERS
        )
        response_data = response.json()

        """
        # simulación de la respuesta de transbank
        response_data = {
            "buy_order": f"{entity_name}-{entity_instance.id}",
            "card_detail": {
                "card_number": "1234",
            },
            "accounting_date": "1006",
            "transaction_date": "2021-09-20",
            "details": [
                {
                    "amount": entity_instance.payment_price,
                    "status": "FAILED",
                    "authorization_code": "123456",
                    "payment_type_code": "VN",
                    "response_code": -97,
                    "installments_number": 1,
                    "commerce_code": ONECLICK_TRANSACTION_COMMERCIAL_CODE,
                    "buy_order": f"{entity_name}-{entity_instance.id}",
                }
            ],
        }
        """

        # print("Transacción", response_data)
        details = response_data["details"][0]
        status = details["status"]
        code = details["response_code"]

        if code == 0 and status == "AUTHORIZED":
            correct_transaction = True
        else:
            raise TransactionTransbankException()

    except TransactionTransbankException as e:
        # La transacción no resultó positiva, se revierte los cambios en la base de datos.
        print("Transacción Compra fallida", e, "progreso", progress)
        restore_transaction_validation(
            progress,
            transaction_instance,
            entity_instance,
            entity_table_session,
            user_table_session_instance,
            runner_table_session_instance,
            consumable_history_instances,
            session,
        )

    except requests.exceptions.RequestException as e:
        print("Error creando la transacción", e, "progreso", progress)
        restore_transaction_validation(
            progress,
            transaction_instance,
            entity_instance,
            entity_table_session,
            user_table_session_instance,
            runner_table_session_instance,
            consumable_history_instances,
            session,
        )
        raise request_exception(
            detail="ERROR NETWORK",
            status_code=502,
        )

    except Exception as e:
        # Error desconocido, se revierte los cambios en la base de datos.
        print("Transacción Error General", e, "progreso", progress)
        restore_transaction_validation(
            progress,
            transaction_instance,
            entity_instance,
            entity_table_session,
            user_table_session_instance,
            runner_table_session_instance,
            consumable_history_instances,
            session,
        )
        if paid:
            # Actualizar el estado de la transacción en la tabla TransactionWebpay
            transformed_response_data = (
                {
                    "transaction_id": transaction_instance.id,
                    "buy_order": response_data["buy_order"]
                    if response_data.get("buy_order")
                    else None,
                    "card_number": response_data["card_detail"]["card_number"]
                    if response_data.get("card_detail")
                    else None,
                    "accounting_date": response_data["accounting_date"]
                    if response_data.get("accounting_date")
                    else None,
                    "transaction_date": response_data["transaction_date"]
                    if response_data.get("transaction_date")
                    else None,
                    "amount": details["amount"],
                    "status": details["status"],
                    "authorization_code": details["authorization_code"],
                    "payment_type_code": details["payment_type_code"],
                    "response_code": details["response_code"],
                    "installments_number": details["installments_number"],
                    "commerce_code": details["commerce_code"],
                    "buy_order_commerce": details["buy_order"],
                }
                if details
                else {
                    "transaction_id": transaction_instance.id,
                    "buy_order": response_data["buy_order"]
                    if response_data.get("buy_order")
                    else None,
                    "card_number": response_data["card_detail"]["card_number"]
                    if response_data.get("card_detail")
                    else None,
                    "accounting_date": response_data["accounting_date"]
                    if response_data.get("accounting_date")
                    else None,
                    "transaction_date": response_data["transaction_date"]
                    if response_data.get("transaction_date")
                    else None,
                    "amount": entity_instance.payment_price,
                    "commerce_code": ONECLICK_TRANSACTION_COMMERCIAL_CODE,
                    "buy_order_commerce": f"{entity_name}-{entity_instance.id}",
                }
            )
            refund_response = refund_oneclick_transaction(transformed_response_data)
            # print("Refund response", refund_response)
            transformed_response_data["status"] = (
                refund_response["response"].get("type")
                if refund_response["response"].get("type")
                else "ERROR"
            )
            if transformed_response_data["status"] == "NULLIFIED":
                transformed_response_data["authorization_code"] = refund_response[
                    "response"
                ].get("authorization_code")
                transformed_response_data["response_code"] = refund_response[
                    "response"
                ].get("response_code")
            transformed_response_data["restaurant_mall_mode"] = (
                commerce_code is not None
            )
            session.create(TransactionOneclick, transformed_response_data)
        raise request_exception(
            detail="ERROR SERVIDOR",
            status_code=500,
        )

    # Llenar los metadatos de la transacción de webpay en la tabla TransactionWebpay
    transformed_response_data = {
        "transaction_id": transaction_instance.id,
        "buy_order": response_data["buy_order"]
        if response_data.get("buy_order")
        else None,
        "card_number": response_data["card_detail"]["card_number"]
        if response_data.get("card_detail")
        else None,
        "accounting_date": response_data["accounting_date"]
        if response_data.get("accounting_date")
        else None,
        "transaction_date": response_data["transaction_date"]
        if response_data.get("transaction_date")
        else None,
        "amount": details["amount"],
        "status": details["status"],
        "authorization_code": details["authorization_code"],
        "payment_type_code": details["payment_type_code"],
        "response_code": details["response_code"],
        "installments_number": details["installments_number"],
        "commerce_code": details["commerce_code"],
        "buy_order_commerce": details["buy_order"],
        "restaurant_mall_mode": commerce_code is not None,
    }

    transaction_oneclick_instance = session.create(
        TransactionOneclick, transformed_response_data
    )

    # Si la transacción se concretó correctamente, modifica la entidad especificada con un payment_status pagado.
    if correct_transaction:
        try:
            html_content = create_html_content(status)
            return HTMLResponse(content=html_content, status_code=200)
        except Exception as e:
            # Si hay un error al momento de guardar los datos de la compra, se regresa un error.
            # Se revierte la transacción
            session.db.rollback()
            refund_response = refund_oneclick_transaction(transformed_response_data)
            transformed_response_data["status"] = refund_response["response"].get(
                "type"
            )
            if transformed_response_data["status"] == "NULLIFIED":
                transformed_response_data["authorization_code"] = refund_response[
                    "response"
                ].get("authorization_code")
                transformed_response_data["response_code"] = refund_response[
                    "response"
                ].get("response_code")
            session.update(transaction_oneclick_instance, transformed_response_data)
            # Si hay un error al momento de guardar los datos de la compra, se regresa un error.
            print("Error al guardar los datos de la compra", e)
            raise request_exception(
                detail="ERROR SERVIDOR, ANULADO",
                status_code=502,
            )
    else:
        # session.update(transaction_instance, {"done": False})
        # Status code = 200 pues el error proviene de Transbank, no de la aplicación. Y en el frontend se manejará
        if code == -96:
            raise request_exception(
                detail="NO EXISTE",
                status_code=404,
            )
        elif code == -97:
            raise request_exception(
                detail="LIMITE DIARIO",
                status_code=405,
            )
        elif code == -98:
            raise request_exception(
                detail="LIMITE DE MONTO",
                status_code=405,
            )
        elif code == -99:
            raise request_exception(
                detail="LIMITE DE PAGOS",
                status_code=405,
            )
        else:
            raise request_exception(
                detail="ERROR DESCONOCIDO",
                status_code=400,
            )


# TODO: Sería conveniente pasarle el entity name y entity id en el payload, para así obtener la entidad creada con ese precio
# cambiarle el estado a refund y obtener su amount desde ahí mismo, para que no metan cualquier número.
def refund_oneclick_transaction(transaction_instance: dict):
    payload = {
        "amount": transaction_instance["amount"],
        "commerce_code": transaction_instance["commerce_code"],
        "detail_buy_order": transaction_instance["buy_order_commerce"],
    }
    response = requests.post(
        f"{TRANSBANK_API_ONECLICK_TRANSACTION_URL}/{transaction_instance['buy_order']}/refunds",
        json=payload,
        headers=HEADERS,
    )
    response_data = response.json()
    return {
        "buy_order": transaction_instance["buy_order"],
        "amount": transaction_instance["amount"],
        "response": response_data,
    }
