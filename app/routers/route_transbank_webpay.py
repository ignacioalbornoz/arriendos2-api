#from typing import Optional
from fastapi import APIRouter
#from fastapi import APIRouter, Depends
# from dependencies.transactions import get_transaction_instance_from_token_using_query
# from repository.transbank_webpay_transactions import (
#     commit_tbk_transaction,
#     commit_tbk_mall_transaction,
#     get_tbk_transaction,
#     get_tbk_mall_transaction,
#     refund_tbk_instance,
#     refund_tbk_mall_instance,
#     create_html_content,
# )
# from repository.transbank_webpay_transactions_local import (
#     get_transaction_entity,
#     approve_transaction_entity,
#     get_user_table_session_by_entity,
#     activate_user_table_session,
#     get_consumables_by_order_id,
#     update_consumables_to_en_fila,
#     restore_transaction_validation,
# )
# from repository.exceptions import TransactionTransbankException
# from fastapi.responses import HTMLResponse

# from shared_models.transactions import TransactionWebpay
# from sqlalchemy.future import select


router = APIRouter()


# Ednpoint que se debe llamar en el mismo instante que una transacción se concreta, ya sea
# porque se completó el flujo de compra o porque se abortó manualmente.
# @router.get("/webpaytransaction/commit")
# def webpay_plus_commit(
#     token_ws: Optional[str] = None,
#     TBK_TOKEN: Optional[str] = None,
#     transaction_instances=Depends(get_transaction_instance_from_token_using_query),
#     session: SessionDAL = Depends(get_generic_session),
# ):
#     transaction_instance, transaction_webpay_instance, commerce_code = (
#         transaction_instances
#     )
#     token = token_ws if token_ws else TBK_TOKEN
#     if not token:
#         html_content = create_html_content("TIMEOUT")
#         return HTMLResponse(content=html_content, status_code=408)

#     # Si no hay token o si ya se realizó la transacción con este token, retorna el estado final.
#     if not transaction_instance or not transaction_webpay_instance:
#         # return {'token': token, 'response': response_data}
#         # msg= 'No se pudo realizar tu transacción, probablemente porque dejaste pasar mucho tiempo desde su creación'
#         # color='red'
#         html_content = create_html_content("ERROR INTERNO")
#         return HTMLResponse(content=html_content, status_code=400)
#     elif transaction_instance.done:
#         # return {'token': token, 'response': response_data}
#         # msg= 'Tu pago ya fue realizado con éxito anteriormente'
#         # color='green'
#         html_content = create_html_content(transaction_webpay_instance.status)
#         return HTMLResponse(content=html_content, status_code=200)

#     # Si se recibe un TBK_TOKEN, entonces hubo un error en el formulario de pago.
#     if TBK_TOKEN:
#         response_data = {}
#         # Se obtiene el estado de la transacción
#         if commerce_code:
#             response_data = commit_tbk_mall_transaction(TBK_TOKEN)
#         else:
#             response_data = commit_tbk_transaction(TBK_TOKEN)
#         # Se verifica si la transacción fue abortada por el usuario
#         if response_data.get("error_message").find("aborted") > -1:
#             html_content = create_html_content("ANULADA")
#             return HTMLResponse(content=html_content, status_code=402)
#         # Si no fue abortada, se informa al usuario que hubo un error en la transacción
#         else:
#             html_content = create_html_content("ERROR DESCONOCIDO")
#             return HTMLResponse(content=html_content, status_code=400)

#     # Al llegar aquí, no hay errores en el formulario de pago, se procede a obtener los datos en la base de datos.
#     response_data = {"response_code": -999}
#     try:
#         # Se actualiza la entidad
#         if commerce_code:
#             response_data = get_tbk_mall_transaction(token)

#             details = response_data.get("details", [])
#             if len(details) == 0:
#                 html_content = create_html_content("ERROR INTERNO")
#                 return HTMLResponse(content=html_content, status_code=400)
#             detail: dict = details[0]

#             # Actualizar el estado de la transacción en la tabla TransactionWebpayMall
#             transformed_response_data = {
#                 "vci": response_data.get("vci"),
#                 "buy_order": response_data.get("buy_order"),
#                 "session_id": response_data.get("session_id"),
#                 "accounting_date": response_data.get("accounting_date"),
#                 "transaction_date": response_data.get("transaction_date"),
#                 "card_number": response_data.get("card_detail", {}).get(
#                     "card_number", None
#                 ),
#                 "amount": detail.get("amount"),
#                 "status": detail.get("status"),
#                 "authorization_code": detail.get("authorization_code"),
#                 "payment_type_code": detail.get("payment_type_code"),
#                 "response_code": detail.get("response_code"),
#                 "installments_number": detail.get("installments_number"),
#                 "commerce_code": detail.get("commerce_code"),
#                 "buy_order_commerce": detail.get("buy_order"),
#             }
#             session.update(transaction_webpay_instance, transformed_response_data)

#         else:
#             response_data = get_tbk_transaction(token)

#             # Actualizar el estado de la transacción en la tabla TransactionWebpay
#             transformed_response_data = {
#                 "vci": response_data.get("vci"),
#                 "amount": response_data.get("amount"),
#                 "status": response_data.get("status"),
#                 "buy_order": response_data.get("buy_order"),
#                 "session_id": response_data.get("session_id"),
#                 "card_number": response_data.get("card_detail", {}).get(
#                     "card_number", None
#                 ),
#                 "accounting_date": response_data.get("accounting_date"),
#                 "transaction_date": response_data.get("transaction_date"),
#                 "authorization_code": response_data.get("authorization_code"),
#                 "payment_type_code": response_data.get("payment_type_code"),
#                 "response_code": response_data.get("response_code"),
#                 "installments_number": response_data.get("installments_number"),
#             }
#             session.update(transaction_webpay_instance, transformed_response_data)

#         # Obtenemos la información de la transacción:
#         entity_name, entity_id = response_data["buy_order"].split("-")
#         user_table_session_id = response_data["session_id"]
#         entity_instance = get_transaction_entity(entity_name, entity_id, session)
#         if not entity_instance:
#             html_content = create_html_content("ERROR SERVIDOR")
#             return HTMLResponse(content=html_content, status_code=404)
#         if entity_name == "order":
#             user_table_session_instance, runner_instance = (
#                 get_user_table_session_by_entity(
#                     entity_name, user_table_session_id, session
#                 )
#             )
#             consumable_history_instances = get_consumables_by_order_id(
#                 entity_id, session
#             )

#     except Exception as e:
#         print("Error en la transacción", e)
#         html_content = create_html_content("ERROR SERVIDOR")
#         return HTMLResponse(content=html_content, status_code=502)

#     # Preprocesamos la transacción, suponiendo que no hay errores y que se concretará.
#     correct_transaction = False
#     paid = False
#     progress = 0
#     entity_table_session = None
#     runner_table_session_instance = None
#     try:
#         # Se marca la transacción con un status done=True.
#         session.update(transaction_instance, {"done": True})
#         progress = 1

#         # Se aprueba la entidad
#         entity_table_session = approve_transaction_entity(
#             entity_name, entity_instance, user_table_session_id, session
#         )
#         progress = 2

#         # Si la entidad es una orden, se actualizan los consumibles a "en fila"
#         if entity_name == "order":
#             update_consumables_to_en_fila(consumable_history_instances, session)
#             progress = 3

#             # Se activa la sesión de la mesa si es la primera compra
#             if user_table_session_instance and runner_instance:
#                 runner_table_session_instance = activate_user_table_session(
#                     user_table_session_instance, runner_instance, session
#                 )
#                 progress = 4
#         # Confirmar la transacción en Transbank
#         paid = True
#         code = -999
#         status = "ERROR"
#         if commerce_code:
#             response_data = commit_tbk_mall_transaction(token)
#             details = response_data.get("details", [])
#             if len(details) == 0:
#                 html_content = create_html_content("ERROR INTERNO")
#                 return HTMLResponse(content=html_content, status_code=400)
#             detail: dict = details[0]
#             code = detail.get("response_code")
#             status = detail.get("status")
#         else:
#             response_data = commit_tbk_transaction(token)
#             code = response_data.get("response_code")
#             status = response_data.get("status")
#         if code == 0 and status == "AUTHORIZED":
#             correct_transaction = True
#         else:
#             raise TransactionTransbankException()
#     except TransactionTransbankException as e:
#         # La transacción no resultó positiva, se revierte los cambios en la base de datos.
#         print("Transacción Compra fallida", e, "progreso", progress)
#         restore_transaction_validation(
#             progress,
#             transaction_instance,
#             entity_instance,
#             entity_table_session,
#             user_table_session_instance,
#             runner_table_session_instance,
#             consumable_history_instances,
#             session,
#         )

#     except Exception as e:
#         # Error desconocido, se revierte los cambios en la base de datos.
#         print("Transacción Error General", e, "progreso", progress)
#         restore_transaction_validation(
#             progress,
#             transaction_instance,
#             entity_instance,
#             entity_table_session,
#             user_table_session_instance,
#             runner_table_session_instance,
#             consumable_history_instances,
#             session,
#         )
#         if paid:
#             # Se actualiza la entidad
#             transformed_response_data = {}
#             if commerce_code:
#                 details = response_data.get("details", [])
#                 if len(details) == 0:
#                     html_content = create_html_content("ERROR INTERNO")
#                     return HTMLResponse(content=html_content, status_code=400)
#                 detail: dict = details[0]

#                 # Actualizar el estado de la transacción en la tabla TransactionWebpayMall
#                 transformed_response_data = {
#                     "vci": response_data.get("vci"),
#                     "buy_order": response_data.get("buy_order"),
#                     "session_id": response_data.get("session_id"),
#                     "accounting_date": response_data.get("accounting_date"),
#                     "transaction_date": response_data.get("transaction_date"),
#                     "card_number": response_data.get("card_detail", {}).get(
#                         "card_number", None
#                     ),
#                     "amount": detail.get("amount"),
#                     "status": detail.get("status"),
#                     "authorization_code": detail.get("authorization_code"),
#                     "payment_type_code": detail.get("payment_type_code"),
#                     "response_code": detail.get("response_code"),
#                     "installments_number": detail.get("installments_number"),
#                     "commerce_code": detail.get("commerce_code"),
#                     "buy_order_commerce": detail.get("buy_order"),
#                 }

#             else:
#                 # Actualizar el estado de la transacción en la tabla TransactionWebpay
#                 transformed_response_data = {
#                     "vci": response_data.get("vci"),
#                     "amount": response_data.get("amount"),
#                     "status": response_data.get("status"),
#                     "buy_order": response_data.get("buy_order"),
#                     "session_id": response_data.get("session_id"),
#                     "card_number": response_data.get("card_detail", {}).get(
#                         "card_number", None
#                     ),
#                     "accounting_date": response_data.get("accounting_date"),
#                     "transaction_date": response_data.get("transaction_date"),
#                     "authorization_code": response_data.get("authorization_code"),
#                     "payment_type_code": response_data.get("payment_type_code"),
#                     "response_code": response_data.get("response_code"),
#                     "installments_number": response_data.get("installments_number"),
#                 }

#             refund_response = {}
#             if commerce_code:
#                 refund_response = refund_tbk_mall_instance(transaction_webpay_instance)
#             else:
#                 refund_response = refund_tbk_instance(transaction_webpay_instance)
#             # print("Refund response", refund_response)
#             transformed_response_data["status"] = (
#                 refund_response["response"].get("type")
#                 if refund_response["response"].get("type")
#                 else "ERROR"
#             )

#             if transformed_response_data["status"] == "NULLIFIED":
#                 transformed_response_data["authorization_code"] = refund_response[
#                     "response"
#                 ].get("authorization_code")
#                 transformed_response_data["response_code"] = refund_response[
#                     "response"
#                 ].get("response_code")
#             session.update(transaction_webpay_instance, transformed_response_data)
#         html_content = create_html_content("ERROR SERVIDOR")
#         return HTMLResponse(content=html_content, status_code=500)

#     # Actualizar el estado de la transacción en la tabla TransactionWebpay
#     transformed_response_data = {}
#     status = ""
#     code = -999
#     if commerce_code:
#         details = response_data.get("details", [])
#         if len(details) == 0:
#             html_content = create_html_content("ERROR INTERNO")
#             return HTMLResponse(content=html_content, status_code=400)
#         detail: dict = details[0]

#         # Actualizar el estado de la transacción en la tabla TransactionWebpayMall
#         transformed_response_data = {
#             "vci": response_data.get("vci"),
#             "buy_order": response_data.get("buy_order"),
#             "session_id": response_data.get("session_id"),
#             "accounting_date": response_data.get("accounting_date"),
#             "transaction_date": response_data.get("transaction_date"),
#             "card_number": response_data.get("card_detail", {}).get(
#                 "card_number", None
#             ),
#             "amount": detail.get("amount"),
#             "status": detail.get("status"),
#             "authorization_code": detail.get("authorization_code"),
#             "payment_type_code": detail.get("payment_type_code"),
#             "response_code": detail.get("response_code"),
#             "installments_number": detail.get("installments_number"),
#             "commerce_code": detail.get("commerce_code"),
#             "buy_order_commerce": detail.get("buy_order"),
#         }
#         status = detail.get("status")
#         code = detail.get("response_code")
#     else:
#         # Actualizar el estado de la transacción en la tabla TransactionWebpay
#         transformed_response_data = {
#             "vci": response_data.get("vci"),
#             "amount": response_data.get("amount"),
#             "status": response_data.get("status"),
#             "buy_order": response_data.get("buy_order"),
#             "session_id": response_data.get("session_id"),
#             "card_number": response_data.get("card_detail", {}).get(
#                 "card_number", None
#             ),
#             "accounting_date": response_data.get("accounting_date"),
#             "transaction_date": response_data.get("transaction_date"),
#             "authorization_code": response_data.get("authorization_code"),
#             "payment_type_code": response_data.get("payment_type_code"),
#             "response_code": response_data.get("response_code"),
#             "installments_number": response_data.get("installments_number"),
#         }
#         status = response_data.get("status")
#         code = response_data.get("response_code")
#     session.update(transaction_webpay_instance, transformed_response_data)

#     # Si la transacción se concretó correctamente, modifica la entidad especificada con un payment_status pagado.
#     if correct_transaction:
#         try:
#             html_content = create_html_content(status)
#             return HTMLResponse(content=html_content, status_code=200)
#         except Exception as e:
#             # Si hay un error al momento de guardar los datos de la compra, se regresa un error.
#             # Se revierte la transacción
#             refund_response = {}
#             if commerce_code:
#                 refund_response = refund_tbk_mall_instance(transaction_webpay_instance)
#             else:
#                 refund_response = refund_tbk_instance(transaction_webpay_instance)
#             # print("Refund response", refund_response)
#             transformed_response_data["status"] = refund_response["response"].get(
#                 "type"
#             )
#             if transformed_response_data["status"] == "NULLIFIED":
#                 transformed_response_data["authorization_code"] = refund_response[
#                     "response"
#                 ].get("authorization_code")
#                 transformed_response_data["response_code"] = refund_response[
#                     "response"
#                 ].get("response_code")
#             session.update(transaction_webpay_instance, transformed_response_data)
#             print("Error al guardar los datos de la compra", e)
#             html_content = create_html_content("ERROR SERVIDOR, ANULADA")
#             return HTMLResponse(content=html_content, status_code=502)

#     # Hubo un error en la transacción.
#     if code == -1:
#         html_content = create_html_content("ERROR")
#         return HTMLResponse(content=html_content, status_code=405)
#     elif code == -2:
#         html_content = create_html_content("RECHAZADA")
#         return HTMLResponse(content=html_content, status_code=405)
#     elif code == -3:
#         html_content = create_html_content("ERROR INTERNO")
#         return HTMLResponse(content=html_content, status_code=400)
#     elif code == -4:
#         html_content = create_html_content("CANCELADA")
#         return HTMLResponse(content=html_content, status_code=403)
#     elif code == -5:
#         html_content = create_html_content("RIESGO")
#         return HTMLResponse(content=html_content, status_code=403)
#     else:
#         html_content = create_html_content("ERROR DESCONOCIDO")
#         return HTMLResponse(content=html_content, status_code=400)


# # # Supuesto endpoint de redirect error, diría que está deprecado xd
# # @router.post("/webpaytransaction/redirect")
# # def webpay_plus_commit_error(token_ws: str):
# #     return {"token": token_ws, "response": {"error": "Transacción con errores"}}


# # # Obtiene el estado actual de una transacción tbk a través del un token_ws.
# # @router.get("/webpaytransaction/status")
# # def webpay_plus_status(token_ws: str):
# #     response_data = get_tbk_transaction(token_ws)
# #     return {"token": token_ws, "response": response_data}


# # # No lo he probado...
# # @router.post("/webpaytransaction/{token_ws}/refund")
# # def webpay_plus_refund(token_ws, amount: str):
# #     return refund_tbk_transaction(token_ws, amount)


# @router.get("/queso")
# def aleluya():
#     html_content = """
#         <html>
#         <head>
#             <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
#             <title>Ejemplos Webpay Plus - Crear Transaccion</title>
#             {% include 'include/header.html' %}
#         </head>

#         <body class="container">
#             <nav aria-label="breadcrumb">
#             <ol class="breadcrumb">
#             <li class="breadcrumb-item"><a href="#">Ejemplo Webpay Plus - Crear Transaccion</a></li>
#             <li class="breadcrumb-item active" aria-current="page">Step: <strong>Create Transaction</strong></li>
#             </ol>
#             </nav>


#             <div class="alert alert-warning" role="alert">
#             <h3>request</h3>
#                 {% for k, v in request.items() %}
#                     {{ k }} = {{ v }},
#                 {% endfor %}
#         </div>
#             <div class="alert alert-primary" role="alert">
#             <h3>result</h3>
#             {{ response }}
#         </div>
#         <br>
#         <form action="https://webpay3g.transbank.cl/webpayserver/initTransaction" method="POST">
#         <input name="token_ws" value="{{ response.token }}">
#         <input type="submit" value="Ejecutar Pago con Webpay">
#         </form>
#         <br>

#         <a href="/">&laquo; volver a index</a>
#         </body>
#         </html>
#     """
#     return HTMLResponse(content=html_content, status_code=200)
