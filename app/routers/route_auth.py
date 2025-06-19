from fastapi import APIRouter
router = APIRouter()


# Recibe el access_token proporcionado por Google en el header, obtiene al User
# en la base de datos (o lo crea si no existe) y genera un access_token de
# Clicomo a partir de su id.
# check terms accepted
