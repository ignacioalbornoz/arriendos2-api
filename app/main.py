# Import statements for third-party libraries
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.route_base import api_router
import os


def init_app():
    TITLE = os.getenv("TITLE")
    if TITLE is None:
        raise EnvironmentError("The environment variable TITLE is not defined.")
    app = FastAPI(
        # openapi_tags=tags_metadata,
        title=TITLE,
        description="Arriendos2 API",
        version="0.1",
    )

    app.include_router(api_router)

    allowed_origins = [
        "http://localhost",
        "*",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origins=allowed_origins,
    )

    return app


app = init_app()

# Check if the database needs to be populated
if __name__ == "__main__":
    # Uncomment the following line if you want to populate the database on startup
    MODE = os.getenv("MODE")
    if MODE is None:
        raise EnvironmentError("The environment variable MODE is not defined.")
    # if MODE == "DEV":
    #     populate_database(
    #         populate_images_flag=False
    #     ) 
    else:
        print("No fue necesario poblar la base de datos")
    uvicorn.run("main:app", port=8080, host="0.0.0.0", reload=True)
