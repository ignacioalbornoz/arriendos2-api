from fastapi import APIRouter


router = APIRouter()


# # Get the current ask again status, if it doesn't exist, create it
# @router.get("/getAskOneclick", response_model=UserOneclickAddOnResponse)
# def get_ask_again_status(session: SessionDAL = Depends(get_user_table_session)):
#     ask_status = oneclick_ask.get_oneclick_ask(session)
#     if ask_status:
#         ask_status = ask_status[0]

#     # If ask_status doesn't exist, create a new one
#     if not ask_status:
#         ask_status = oneclick_ask.create_or_update_oneclick_ask(
#             user_id=session.user.id, declined=False, session=session
#         )

#     # Return the ask status
#     return UserOneclickAddOnResponse(
#         user_id=session.user.id, declined=ask_status.declined
#     )


# # Create or update the ask again status
# @router.put("/updateAsk", response_model=UserOneclickAddOnResponse)
# def update_ask_again_status(
#     update_data: UserOneclickAddOnUpdate,
#     session: SessionDAL = Depends(get_user_table_session),
# ):
#     updated_record = oneclick_ask.create_or_update_oneclick_ask(
#         session.user.id, update_data.declined, session
#     )
#     return UserOneclickAddOnResponse(
#         user_id=session.user.id, declined=updated_record.declined
#     )
