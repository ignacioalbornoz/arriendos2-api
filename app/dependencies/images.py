from fastapi import Depends, UploadFile
from pydantic import PositiveInt
from dependencies.session import (
    get_user_restaurant_session,
    UserRestaurantSessionGetter,
)
from dependencies.base import (
    get_model_instance,
    get_model_instance_by_id_in_form,
    verify_condition,
)
from shared_models.images import Image
from repository.session import SessionDAL
from repository.images import get_image_by_path_name, get_image_by_id
from shared_schemas.menus.menu_categories import MenuCategoryCreate, MenuCategoryUpdate
from shared_schemas.menus.menu_items import MenuItemCreate, MenuItemUpdate


MAX_FILE_SIZE = 1e7  # límite 10 mb
get_session_with_image_perm = UserRestaurantSessionGetter(Image)


# Obtiene una instancia de Image a partir de su path_name especificado en el path.
def get_image_instance_by_path_name_using_path(
    path_name: str, session: SessionDAL = Depends(get_user_restaurant_session)
):
    return get_model_instance(get_image_by_path_name, path_name, session=session)


# Obtiene una instancia de Image a partir de su path_name especificado en el path.
def get_image_instance_by_id_using_path(
    id: PositiveInt, session: SessionDAL = Depends(get_user_restaurant_session)
):
    return get_model_instance(get_image_by_id, id, session=session)


# Obtiene una instancia de Image a partir de su id especificado en el payload.
def get_image_instance_using_payload(
    payload: MenuCategoryCreate | MenuCategoryUpdate | MenuItemCreate | MenuItemUpdate,
    session: SessionDAL = Depends(get_user_restaurant_session),
):
    return get_model_instance_by_id_in_form(
        Image, payload, session, primary_key_name="image_id"
    )


# Retorna el formato de la Image si file es una Image válida; en otro caso arroja error.
def get_file_extension(file: UploadFile):
    image_magic_bytes = {
        b"\xff\xd8\xff": "jpeg",
        b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a": "png",
        b"GIF87a": "gif",
        b"GIF89a": "gif",
        b"RIFF": "webp",
        b"WEBP": "webp",
    }
    file_bytes = file.file
    file_bytes.seek(0)
    magic_bytes = file_bytes.read(12)
    file_extension = None
    for signature, image_format in image_magic_bytes.items():
        if magic_bytes.startswith(signature):
            file_extension = image_format
    verify_condition(
        lambda file_extension: file_extension,
        file_extension,
        detail="Invalid file extension.",
    )
    return file_extension


# Verifica que el tamaño de la Image no exceda el tamaño máximo permitido.
def verify_file_size(file: UploadFile):
    file_bytes = file.file
    file_bytes.seek(0)
    file_bytes.seek(0, 2)
    file_size = file_bytes.tell()
    verify_condition(
        lambda file_size: file_size <= MAX_FILE_SIZE,
        file_size,
        detail="File size exceeds the limit.",
    )


# Verifica que el largo del real_name de la Image no sea mayor al máximo permitido.
def verify_filename(file: UploadFile):
    verify_condition(
        lambda file: len(file.filename) <= 150, file, detail="filename is too large."
    )
