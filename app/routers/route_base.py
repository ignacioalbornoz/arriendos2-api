from fastapi import APIRouter

from routers import (
    route_auth,
    route_transbank_webpay,
    route_transbank_oneclick,
    route_oneclick_cards,
    route_oneclick_user_ask,
)
# from fastapi.responses import FileResponse
# import os

api_router = APIRouter()


@api_router.get("/")
def root():
    return "API OK"


# @api_router.get("/templates/favicon.ico")
# def favicon():
#     file_path = os.path.join(os.getcwd(), "templates", "favicon.ico")
#     return FileResponse(file_path, media_type="image/x-icon")


api_router.include_router(route_auth.router, prefix="/auth", tags=["auth"])



api_router.include_router(route_transbank_webpay.router, tags=["Webpay"])
api_router.include_router(route_transbank_oneclick.router, tags=["Oneclick"])
api_router.include_router(
    route_oneclick_cards.router, prefix="/oneclick_cards", tags=["Oneclick Cards"]
)
api_router.include_router(
    route_oneclick_user_ask.router, prefix="/oneclick_ask", tags=["Ask Oneclick"]
)

