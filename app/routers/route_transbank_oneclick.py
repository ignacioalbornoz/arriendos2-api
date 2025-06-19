from fastapi import APIRouter

router = APIRouter()


# # Ednpoint que se debe llamar en el mismo instante que una inscripción de oneclick se concreta, ya sea
# # porque se completó el flujo o porque se abortó manualmente.
# @router.get("/oneclickinscription/commit")
# def oneclickinscription_commit(
#     TBK_TOKEN: str = None,
#     TBK_ORDEN_COMPRA: str = None,
#     inscription_instance=Depends(
#         get_oneclick_inscription_instance_from_token_using_query
#     ),
#     session: SessionDAL = Depends(get_generic_session),
# ):
#     token = TBK_TOKEN

#     # Solo llega el token de compra si la transacción fue abortada por el usuario.
#     if TBK_ORDEN_COMPRA:
#         html_content = create_html_content("ANULADA")
#         return HTMLResponse(content=html_content, status_code=402)

#     # Si no hay token o si ya se realizó la transacción con este token, retorna el estado final.
#     elif not token:
#         # return {'token': token, 'response': response_data}
#         # msg= 'No se pudo realizar tu transacción, probablemente porque dejaste pasar mucho tiempo desde su creación'
#         # color='red'
#         html_content = create_html_content("ERROR INTERNO")
#         return HTMLResponse(content=html_content, status_code=400)
#     elif inscription_instance.done:
#         # return {'token': token, 'response': response_data}
#         # msg= 'Tu pago ya fue realizado con éxito anteriormente'
#         # color='green'
#         html_content = create_html_content("ERROR TARJETA")
#         return HTMLResponse(content=html_content, status_code=400)

#     response_data = commit_oneclick_inscription(token)

#     # Si la transacción se concretó correctamente, modifica la entidad especificada con un payment_status pagado.
#     if response_data.get("response_code") == 0:
#         try:
#             payload = {
#                 "oneclick_token": response_data["tbk_user"],
#                 "card_type": response_data["card_type"],
#                 "card_number": response_data["card_number"],
#             }

#             oneclick_card_instance = session.get_by_id(
#                 select(OneClickCard),
#                 OneClickCard,
#                 inscription_instance.oneclick_card_id,
#             )
#             session.update(oneclick_card_instance, payload)

#             # Al terminar la inscripción, se comitean los cambios y se marca la transacción con un status done=True.
#             session.update(inscription_instance, {"done": True})

#             html_content = create_html_content(response_data["response_code"])
#             return HTMLResponse(content=html_content, status_code=200)
#         except Exception:
#             # Si hay un error al momento de guardar los datos de la compra, se regresa un error.
#             html_content = create_html_content("ERROR")
#             return HTMLResponse(content=html_content, status_code=500)
#     elif response_data.get("response_code") and response_data.get("response_code") < 0:
#         # Eliminar inscripción si la transacción falló.
#         session.delete_from_query(
#             delete(OneClickInscription).where(
#                 OneClickInscription.oneclick_card_id
#                 == inscription_instance.oneclick_card_id
#             ),
#             commit=False,
#         )
#         session.delete_from_query(
#             delete(OneClickCard).where(
#                 OneClickCard.id == inscription_instance.oneclick_card_id
#             )
#         )
#         # Informar al usuario que hubo un error en la transacción.
#         code = response_data.get("response_code")
#         if code == -1:
#             html_content = create_html_content("ERROR")
#             return HTMLResponse(content=html_content, status_code=405)
#         elif code == -2:
#             html_content = create_html_content("RECHAZADA")
#             return HTMLResponse(content=html_content, status_code=405)
#         elif code == -3:
#             html_content = create_html_content("ERROR INTERNO")
#             return HTMLResponse(content=html_content, status_code=400)
#         elif code == -4:
#             html_content = create_html_content("CANCELADA")
#             return HTMLResponse(content=html_content, status_code=403)
#         elif code == -5:
#             html_content = create_html_content("RIESGO")
#             return HTMLResponse(content=html_content, status_code=403)
#         elif code == -96:
#             html_content = create_html_content("TIMEOUT")
#             return HTMLResponse(content=html_content, status_code=405)
#         else:
#             html_content = create_html_content("ERROR DESCONOCIDO")
#             return HTMLResponse(content=html_content, status_code=400)

#     else:
#         html_content = create_html_content("ERROR DESCONOCIDO")
#         return HTMLResponse(content=html_content, status_code=400)


# @router.get("/oneclickinscription/create")
# def oneclickinscription_create(
#     session: SessionDAL = Depends(get_user_table_session),
# ):
#     return create_oneclick_inscription(session)


# @router.delete("/oneclickinscription/delete/{oneclick_card_id}")
# def oneclickinscription_delete_card(
#     session: SessionDAL = Depends(get_user_table_session),
#     oneclick_card_instance=Depends(get_oneclick_card_instance_using_path),
# ):
#     return delete_oneclick_card(session, oneclick_card_instance)


# @router.get("/queso_oneclick")
# def aleluya_oneclick():
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
#         <form action="https://webpay3gint.transbank.cl/webpayserver/multicode_inscription.cgi" method="POST">
#         <input name="TBK_TOKEN" value="{{ response.token }}">
#         <input type="submit" value="Ejecutar Pago con Webpay">
#         </form>
#         <br>

#         <a href="/">&laquo; volver a index</a>
#         </body>
#         </html>
#     """
#     return HTMLResponse(content=html_content, status_code=200)
