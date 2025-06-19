from typing import List, Optional
from pydantic import PositiveInt, NonNegativeInt, TypeAdapter
from sqlalchemy.future import select
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse
from dependencies.images import (
    get_session_with_image_perm,
    get_file_extension,
    verify_file_size,
    verify_filename,
    get_image_instance_by_id_using_path,
)
from shared_models.images import Image
from repository.session import SessionDAL
import repository.images as images
from shared_schemas.images import ShowImage, ImageUpdate
from shared_schemas.base import payload_to_dict
from utils.helpers import has_same_values
from repository.exceptions import no_changes_exception

router = APIRouter()


@router.get("", response_model=List[ShowImage])
def get_images(
    skip: Optional[NonNegativeInt] = 0,
    limit: Optional[PositiveInt] = 100,
    session: SessionDAL = Depends(get_session_with_image_perm),
):
    return session.get_all(select(Image), skip, limit)


@router.get("/restaurant", response_model=List[ShowImage])
def get_images_from_restaurant(
    skip: Optional[NonNegativeInt] = 0,
    limit: Optional[PositiveInt] = 100,
    session: SessionDAL = Depends(get_session_with_image_perm),
):
    image_instances = images.get_images_by_restaurant(session, skip, limit)
    show_image_list = TypeAdapter(List[ShowImage]).validate_python(image_instances)

    for show_images in show_image_list:
        show_images.set_full_path()
    return show_image_list


@router.post(
    "",
    dependencies=[Depends(verify_file_size), Depends(verify_filename)],
    response_model=ShowImage,
)
def upload_image(
    file: UploadFile = File(...),
    session: SessionDAL = Depends(get_session_with_image_perm),
    file_extension=Depends(get_file_extension),
):
    return images.create_image_supa(file, file_extension, session)


@router.get("/{id}")
def get_image_file(image_instance=Depends(get_image_instance_by_id_using_path)):
    return FileResponse(images.UPLOAD_DIR / image_instance.path_name)


@router.put("/{id}", response_model=ShowImage)
def update_image(
    payload: ImageUpdate,
    session: SessionDAL = Depends(get_session_with_image_perm),
    image_instance=Depends(get_image_instance_by_id_using_path),
):
    if has_same_values(payload, image_instance):
        raise no_changes_exception
    return session.update(image_instance, payload_to_dict(payload), commit=True)


@router.put(
    "/replace/{id}",
    dependencies=[Depends(verify_file_size), Depends(verify_filename)],
    response_model=ShowImage,
)
def upload_and_replace_image(
    file: UploadFile = File(...),
    session: SessionDAL = Depends(get_session_with_image_perm),
    file_extension=Depends(get_file_extension),
    image_instance=Depends(get_image_instance_by_id_using_path),
):
    return images.replace_image_supa(file, file_extension, image_instance, session)


@router.delete("/{id}")
def delete_image(
    session: SessionDAL = Depends(get_session_with_image_perm),
    image_instance=Depends(get_image_instance_by_id_using_path),
):
    return images.delete_image(image_instance, session)
