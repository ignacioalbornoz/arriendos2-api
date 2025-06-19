

# # Obtiene una lista con las tarjetas inscritas en la aplicación para el usuario que tienen un token oneclick válido.
# def get_oneclick_card(session: SessionDAL):
#     select_query = select(OneClickCard)
#     select_query = select_query.where(
#         OneClickCard.user_id == session.user.id,
#         OneClickCard.oneclick_token.is_not(None),
#     )

#     return session.get_all(select_query)


# # Obtiene las tarjetas asociadas a un usuario con un token oneclick válido.
# def get_oneclick_card_by_user_id(user_id, session: SessionDAL):
#     select_query = select(OneClickCard)
#     select_query = select_query.where(
#         OneClickCard.user_id == user_id,
#         OneClickCard.oneclick_token.is_not(None),
#     )

#     return session.get_all(select_query)
