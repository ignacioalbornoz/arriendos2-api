

# # Obtiene una instancia de Table a partir de su id especificado en el path.
# def get_oneclick_card_instance_using_path(
#     oneclick_card_id: PositiveInt, session: SessionDAL = Depends(get_user_table_session)
# ):
#     return get_model_instance_by_id(OneClickCard, oneclick_card_id, session)


# def get_oneclick_inscription_instance_from_token_using_query(
#     TBK_TOKEN: str = None, session: SessionDAL = Depends(get_generic_session)
# ):
#     def get_from_token(TBK_TOKEN: str, session: SessionDAL):
#         select_query = (
#             select(OneClickInscription)
#             .where(OneClickInscription.token_tbk == TBK_TOKEN)
#             .order_by(OneClickInscription.created_at.asc())
#         )
#         return session.get(select_query)

#     token = TBK_TOKEN
#     return get_model_instance(get_from_token, token, session=session)
