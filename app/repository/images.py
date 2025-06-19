from uuid import uuid4
from pathlib import Path
from sqlalchemy.future import select
from pydantic import PositiveInt, NonNegativeInt
from sqlalchemy import update
from fastapi import UploadFile
from shared_models.images import Image
from shared_models.base import get_all_classes_with_images
from repository.session import SessionDAL
from supabase import create_client, Client
import os
from PIL import Image as PILImage
from io import BytesIO

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PATH = os.getenv("SUPABASE_PATH")
BUCKET_NAME = os.getenv("BUCKET_NAME")
FILE_EXTENSION = os.getenv("FILE_EXTENSION")
IMAGE_MAX_WIDTH = int(os.getenv("IMAGE_MAX_WIDTH"))
IMAGE_MAX_HEIGHT = int(os.getenv("IMAGE_MAX_HEIGHT"))
IMAGE_QUALITY = int(os.getenv("IMAGE_QUALITY"))
MODE = os.getenv("MODE")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

UPLOAD_DIR = Path("images")


def create_image_supa(file: UploadFile, file_extension: str, session: SessionDAL):
    path_name = None
    real_name, _ = os.path.splitext(file.filename)
    while True:
        path_name = f"{session.restaurant_id}-{uuid4()}.{FILE_EXTENSION}"
        select_query = select(Image).where(Image.path_name == path_name)
        if session.get(select_query) is None:
            break
    converted_file = convert_image_from_file(file, FILE_EXTENSION)

    if FILE_EXTENSION == "jpg":
        content_type = {"content-type": "image/jpg"}
    elif FILE_EXTENSION == "jpeg":
        content_type = {"content-type": "image/jpeg"}
    elif FILE_EXTENSION == "png":
        content_type = {"content-type": "image/png"}
    elif FILE_EXTENSION == "webp":
        content_type = {"content-type": "image/webp"}
    if MODE != "DEV":
        # Upload file to Supabase storage bucket
        file_data = converted_file.read()
        # print("responseobtained")
        full_path = f"{SUPABASE_PATH}/{path_name}"
        # print(f"Full path: {full_path}")
        response = supabase.storage.from_(BUCKET_NAME).upload(
            full_path, file_data, file_options=content_type
        )
        # print("responseobtained")
        # print(response)
        if response and response.status_code == 200:
            image_instance = session.create(
                Image, {"real_name": real_name, "path_name": path_name}
            )
        else:
            raise Exception(f"Error uploading file: {response.text}")
        return image_instance
    else:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        image_instance = session.create(
            Image, {"real_name": real_name, "path_name": path_name}
        )
        with open(UPLOAD_DIR / path_name, "wb") as buffer:
            buffer.write(converted_file.read())

        return image_instance


# Cambia una imagen por otra, manteniendo el mismo id
def replace_image_supa(
    file: UploadFile, file_extension: str, image_instance, session: SessionDAL
):
    path_name = None
    while True:
        path_name = f"{session.restaurant_id}-{uuid4()}.{FILE_EXTENSION}"
        select_query = select(Image).where(Image.path_name == path_name)
        if session.get(select_query) is None:
            break
    real_name, _ = os.path.splitext(file.filename)
    if FILE_EXTENSION == "jpg":
        content_type = {"content-type": "image/jpg"}
    elif FILE_EXTENSION == "jpeg":
        content_type = {"content-type": "image/jpeg"}
    elif FILE_EXTENSION == "png":
        content_type = {"content-type": "image/png"}
    elif FILE_EXTENSION == "webp":
        content_type = {"content-type": "image/webp"}
    converted_file = convert_image_from_file(file, FILE_EXTENSION)
    old_path_name = image_instance.path_name
    if MODE != "DEV":
        # Upload file to Supabase storage bucket
        file_data = converted_file.read()
        # print("responseobtained")
        full_path = f"{SUPABASE_PATH}/{path_name}"
        # print(f"Full path: {full_path}")
        response = supabase.storage.from_(BUCKET_NAME).upload(
            full_path, file_data, file_options=content_type
        )
        # print("responseobtained")
        # print(response)
        if response and response.status_code == 200:
            session.update(
                image_instance, {"real_name": real_name, "path_name": path_name}
            )
        else:
            raise Exception(f"Error uploading file: {response.text}")
        # Eliminar imagen antigua de supabase
        response = supabase.storage.from_(BUCKET_NAME).remove(
            f"{SUPABASE_PATH}/{old_path_name}"
        )
        if (
            response
            and "metadata" in response[0]
            and response[0]["metadata"].get("httpStatusCode") == 200
        ):
            session.commit()
            return image_instance
        else:
            raise Exception(f"Error deleting file: {response}")
    else:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        with open(UPLOAD_DIR / path_name, "wb") as buffer:
            buffer.write(converted_file.read())
        session.update(image_instance, {"real_name": real_name, "path_name": path_name})
        session.commit()
        Path(UPLOAD_DIR / old_path_name).unlink()
        return image_instance


# Crea una instancia de Image en la base de datos y guarda la Image binaria en /images.
def create_image(file: UploadFile, file_extension: str, session: SessionDAL):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path_name = None
    real_name, _ = os.path.splitext(file.filename)
    converted_file = convert_image_from_file(file, FILE_EXTENSION)
    while True:
        path_name = f"{session.restaurant_id}-{uuid4()}.png"
        select_query = select(Image).where(Image.path_name == path_name)
        if session.get(select_query) is None:
            break
    image_instance = session.create(
        Image, {"real_name": real_name, "path_name": path_name}
    )
    with open(UPLOAD_DIR / path_name, "wb") as buffer:
        buffer.write(converted_file.read())

    return image_instance


# Obtiene una instancia de Image a partir de su path_name.
def get_image_by_path_name(path_name: str, session: SessionDAL):
    select_query = select(Image).where(Image.path_name == path_name)
    return session.get(select_query)


# Obtiene una instancia de Image a partir de su id.
def get_image_by_id(id: PositiveInt, session: SessionDAL):
    select_query = select(Image).where(Image.id == id)
    return session.get(select_query)


# Elimina una instancia de Image en la base de datos, asigna image_id = 1 (default.png)
# a todas las entidades que tengan asociada esta imagen como llave foránea y elimina la
# Image binaria en /images.
def delete_image(image_instance, session: SessionDAL):
    path_name = image_instance.path_name
    image_id = image_instance.id
    if MODE == "DEV":
        if session.delete(image_instance, commit=False):
            tables = get_all_classes_with_images()
            for table in tables:
                update_query = (
                    update(table).where(table.image_id == image_id).values(image_id=1)
                )
                session.update_from_query(update_query, commit=False)
            session.commit()
            Path(UPLOAD_DIR / path_name).unlink()
            return True
    else:
        if session.delete(image_instance, commit=False):
            tables = get_all_classes_with_images()
            for table in tables:
                update_query = (
                    update(table).where(table.image_id == image_id).values(image_id=1)
                )
                session.update_from_query(update_query, commit=False)
            response = supabase.storage.from_(BUCKET_NAME).remove(
                f"{SUPABASE_PATH}/{path_name}"
            )
            if (
                response
                and "metadata" in response[0]
                and response[0]["metadata"].get("httpStatusCode") == 200
            ):
                # print("responseprint")
                # print(response)
                session.commit()
                return True
            else:
                raise Exception(f"Error deleting file: {response}")


# Converts an image to the desired extension and optimizes it
def convert_image_from_file(
    file: UploadFile,
    target_extension: str,
    max_width=IMAGE_MAX_WIDTH,
    max_height=IMAGE_MAX_HEIGHT,
    quality=IMAGE_QUALITY,
) -> BytesIO:
    # if target_extension.lower() not in VALID_EXTENSIONS:
    #     raise ValueError(f"Invalid target extension: {target_extension}. Must be one of {VALID_EXTENSIONS}")

    # Load the image from the uploaded file
    image = PILImage.open(file.file)

    # Calculate the aspect ratio
    aspect_ratio = image.height / image.width

    # Determine new width and height maintaining the aspect ratio
    if image.width > max_width or image.height > max_height:
        if image.width > max_width:
            new_width = max_width
            new_height = int(new_width * aspect_ratio)
        if new_height > max_height:
            new_height = max_height
            new_width = int(new_height / aspect_ratio)
        image = image.resize((new_width, new_height), PILImage.LANCZOS)

    # Convert image to BytesIO
    output = BytesIO()
    if target_extension.lower() in {"jpg", "jpeg"}:
        image.save(output, target_extension.upper(), quality=quality, optimize=True)
    else:
        image.save(output, target_extension.lower(), quality=quality, optimize=True)
    output.seek(0)

    return output


# Obtiene todas las instancias de imágenes pertenecientes a un restaurant
def get_images_by_restaurant(
    session: SessionDAL, skip: NonNegativeInt, limit: PositiveInt
):
    select_query = select(Image).where(Image.restaurant_id == session.restaurant_id)
    return session.get_all(select_query, skip, limit)
