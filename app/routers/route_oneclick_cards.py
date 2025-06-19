from fastapi import Depends, APIRouter
import repository.oneclick_cards as oneclick_cards
from typing import List


router = APIRouter()


# # Obtiene una lista con los Restaurants de la aplicación.
# @router.get("", response_model=List[ShowOneClickCard])
# def get_oneclick_card(session: SessionDAL = Depends(get_user_table_session)):
#     return oneclick_cards.get_oneclick_card(session)
