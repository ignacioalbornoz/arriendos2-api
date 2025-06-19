from shared_models.sections import Section
from shared_models.menus.menu_categories import MenuCategory
from shared_models.menus.menu_consumables import MenuConsumable
from shared_models.menus.menu_item_consumables import MenuItemConsumable
from shared_models.menus.menu_items import MenuItem
from shared_models.tables import Table
from shared_models.section_masters import SectionMaster
from shared_models.runners import Runner
from shared_models.user_restaurants.restaurants import Restaurant
from shared_models.user_restaurants.user_restaurants import UserRestaurant
from shared_models.user_restaurants.restaurants_financial import RestaurantFinancial
import pandas as pd
import json
from PIL import Image as PILImage
from uuid import uuid4
from pathlib import Path
from shared_models.images import Image
from supabase import create_client, Client
from sqlalchemy.future import select
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
FILE_EXTENSION = os.getenv("FILE_EXTENSION")
IMAGE_MAX_WIDTH = int(os.getenv("IMAGE_MAX_WIDTH"))
IMAGE_MAX_HEIGHT = int(os.getenv("IMAGE_MAX_HEIGHT"))
IMAGE_QUALITY = int(os.getenv("IMAGE_QUALITY"))
MODE = os.getenv("MODE")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

UPLOAD_DIR = Path("images")
SUPABASE_PATH = os.getenv("SUPABASE_PATH")


def process_and_upload_image(
    db,
    image_name_file,
    images_folder_path,
    file_extension,
    restaurant_id,
    populate_images_bool,
):
    if pd.isna(image_name_file):
        return None  # No image to process

    if not populate_images_bool:
        return None

    real_name, _ = os.path.splitext(image_name_file)
    content_type = None

    image_name_file = convert_image(images_folder_path, image_name_file, file_extension)

    # Determine the content type based on the file extension
    if file_extension == "jpg":
        content_type = {"content-type": "image/jpg"}
    elif file_extension == "jpeg":
        content_type = {"content-type": "image/jpeg"}
    elif file_extension == "png":
        content_type = {"content-type": "image/png"}
    elif file_extension == "webp":
        content_type = {"content-type": "image/webp"}

    # Construct the image file path
    image_name = os.path.join(images_folder_path, image_name_file)

    file_data = None
    try:
        with open(image_name, "rb") as image_file:
            file_data = image_file.read()
        print(f"File data for {image_name} has been successfully read.")
    except FileNotFoundError:
        print(f"File {image_name} not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    path_name = None
    while True:
        path_name = f"{restaurant_id}-{uuid4()}.{file_extension}"
        select_query = select(Image).where(Image.path_name == path_name)
        existing_image = db.execute(select_query).scalar_one_or_none()
        if existing_image is None:
            break

    response = supabase.storage.from_(BUCKET_NAME).upload(
        f"{SUPABASE_PATH}/{path_name}", file_data, file_options=content_type
    )
    print(response)

    if response and response.status_code == 200:
        current_image = Image(
            real_name=real_name, path_name=path_name, restaurant_id=restaurant_id
        )
        db.add(current_image)
        db.commit()
        return current_image.id
    else:
        raise Exception(f"Error uploading file: {response.text}")


def load_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def load_if_exists(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    return None


def create_restaurant(db, restaurant_info, users_info):
    user = users_info.get(restaurant_info["creator_email"])
    restaurant_data = {
        "name": restaurant_info["name"],
        "location": restaurant_info["location"],
        "created_by": user.id,
        "company_tax_id": restaurant_info["company_tax_id"],
    }

    # Solo agrega el campo "open" si está presente en restaurant_info
    if "open" in restaurant_info:
        restaurant_data["open"] = restaurant_info["open"]

    restaurant = Restaurant(**restaurant_data)

    db.add(restaurant)
    db.commit()
    return restaurant


def associate_user_restaurants_roles(db, users, roles, restaurant):
    user_roles = {}
    try:
        for role_info in roles:
            user = users.get(role_info["email"])
            if user:
                user_restaurant = UserRestaurant(
                    user_id=user.id, restaurant_id=restaurant.id, role=role_info["role"]
                )
                role = role_info["role"]
                if role not in user_roles:
                    user_roles[role] = []  # Initialize list for the role if not present
                user_roles[role].append(
                    (
                        role_info["email"],
                        role_info.get("working"),
                        role_info.get("area"),
                    )
                )

                db.add(user_restaurant)
        db.commit()
        return user_roles
    except Exception as e:
        db.rollback()
        print(f"Error occurred: {e}")


def create_financial_data(db, restaurant_id, financial_data):
    restaurant_financial = {
        "restaurant_id": restaurant_id,
        "transbank_webpay_commerce_code": financial_data[
            "transbank_webpay_commerce_code"
        ],
        "transbank_oneclick_commerce_code": financial_data[
            "transbank_oneclick_commerce_code"
        ],
    }

    restaurant_financial_instance = RestaurantFinancial(**restaurant_financial)

    db.add(restaurant_financial_instance)
    db.commit()
    return restaurant_financial_instance


def create_menu_items_and_consumables(
    db,
    current_section_name,
    current_section_id,
    restaurant_id,
    category_ids,
    menu_df,
    images_folder_path,
    file_extension,
    populate_images_bool,
):
    cafeteria_menu_df = menu_df[menu_df["Seccion"] == current_section_name]

    # Transform the data into a list of dictionaries
    section_consumables = cafeteria_menu_df.apply(
        lambda row: {
            "name": row["Plato"],
            "price": row["Valor"],
            "preparation_time_minutes": row["TiempoPreparacion"],
            "description": row["Descripcion"],
            "category": row["Categoria"],
            "image_name": row["NombreImagen"],
        },
        axis=1,
    ).tolist()

    # Agregar los datos actualizados a la base de datos
    for consumable in section_consumables:
        new_consumable = MenuConsumable(
            section_id=current_section_id,
            name=consumable["name"],
            # price=consumable["price"],
            preparation_time_minutes=consumable["preparation_time_minutes"],
            description=consumable["description"],
        )
        db.add(new_consumable)
        db.commit()  # Asegúrate de que el objeto se inserte y obtenga un id de la base de datos
        consumable["id"] = new_consumable.id

    for consumable in section_consumables:
        category_name = consumable["category"]
        image_name_file = consumable["image_name"]
        image_id = process_and_upload_image(
            db,
            image_name_file,
            images_folder_path,
            file_extension,
            restaurant_id,
            populate_images_bool,
        )
        if image_id:
            menu_item = MenuItem(
                name=consumable["name"],
                price=consumable["price"],
                description=consumable["description"],
                estimated_time_minutes=consumable["preparation_time_minutes"],
                category_id=category_ids.get(category_name),
                restaurant_id=restaurant_id,
                image_id=image_id,
            )
        else:
            # Create MenuItem with category_id
            menu_item = MenuItem(
                name=consumable["name"],
                price=consumable["price"],
                description=consumable["description"],
                estimated_time_minutes=consumable["preparation_time_minutes"],
                category_id=category_ids.get(category_name),
                restaurant_id=restaurant_id,
            )
        db.add(menu_item)
        db.commit()  # Commit to get the menu_item.id

        # Associate MenuConsumable with MenuItem
        menu_price_item = MenuItemConsumable(
            menu_item_id=menu_item.id, menu_consumable_id=consumable["id"]
        )
        db.add(menu_price_item)

    db.commit()  # Commit after processing all items in the category


def populate_restaurant(
    db,
    users,
    restaurant_path,
    roles_path,
    financial_path,
    csv_path,
    category_images_csv_path,
    images_folder_path,
    file_extension,
    populate_images_bool,
):
    restaurant_data = load_data(restaurant_path)
    user_restaurants_roles_data = load_data(roles_path)
    financial_data = load_if_exists(financial_path)

    # Create restaurants
    new_restaurant = create_restaurant(db, restaurant_data, users)

    # Associate users
    user_roles = associate_user_restaurants_roles(
        db, users, user_restaurants_roles_data["roles"], new_restaurant
    )

    # Create financial data
    if financial_data:
        create_financial_data(db, new_restaurant.id, financial_data)

    # Extract unique categories
    menu_df = pd.read_csv(csv_path)
    dfcategories = pd.read_csv(category_images_csv_path)
    unique_categories = menu_df["Categoria"].unique()

    # Create the list of dictionaries
    menu_categories = [{"name": category} for category in unique_categories]

    category_ids = {}  # Diccionario para almacenar los IDs de las categorías

    for category in menu_categories:
        image_name_file = dfcategories.loc[
            dfcategories["Categoria"] == category["name"], "NombreImagen"
        ].values[0]
        image_id = process_and_upload_image(
            db,
            image_name_file,
            images_folder_path,
            file_extension,
            new_restaurant.id,
            populate_images_bool,
        )
        if image_id:
            new_category = MenuCategory(
                restaurant_id=new_restaurant.id,
                name=category["name"],
                image_id=image_id,
            )
        else:
            new_category = MenuCategory(
                restaurant_id=new_restaurant.id, name=category["name"]
            )

        db.add(new_category)
        db.commit()  # Asumiendo que db.commit() actualiza los objetos con sus IDs de base de datos
        category_ids[category["name"]] = (
            new_category.id
        )  # Almacenar el ID en el diccionario

    # SECTION (MANDATORY), SECTION-MASTERS AND CONSUMIBLES
    for section in restaurant_data["sections"]:
        restaurant_section = Section(
            restaurant_id=new_restaurant.id,
            name=section["name"],
            description=section["description"],
        )
        db.add(restaurant_section)
        db.commit()
        section_masters = user_roles.get("section_master", [])
        if not section_masters:
            section_masters = []
        for section_master in section_masters:
            section_master_email, section_master_working, section_master_area = (
                section_master
            )
            if section_master_area == section["name"]:
                user = users.get(section_master_email)
                restaurant_section_master = SectionMaster(
                    user_id=user.id,
                    section_id=restaurant_section.id,
                    working=section_master_working,
                )
                db.add(restaurant_section_master)
                db.commit()
        # now add menu categories for each section:
        create_menu_items_and_consumables(
            db,
            section["name"],
            restaurant_section.id,
            new_restaurant.id,
            category_ids,
            menu_df,
            images_folder_path,
            file_extension,
            populate_images_bool,
        )

    # RUNNERS
    runners = user_roles.get("runner", [])
    for runner in runners:
        runner_email, runner_working, runner_area = runner
        user = users.get(runner_email)

        restaurant_runner = Runner(
            user_id=user.id, restaurant_id=new_restaurant.id, working=runner_working
        )
        db.add(restaurant_runner)
        db.commit()

    for table in restaurant_data["tables"]:
        restaurant_table = Table(
            restaurant_id=new_restaurant.id,
            table_number=table["table_number"],
            seats=table["seats"],
        )
        db.add(restaurant_table)
        db.commit()


def convert_image(
    images_folder,
    image_file_name,
    target_extension,
    max_width=IMAGE_MAX_WIDTH,
    max_height=IMAGE_MAX_HEIGHT,
    quality=IMAGE_QUALITY,
):
    # Validate the target extension
    valid_extensions = {"jpg", "jpeg", "png", "webp"}
    if target_extension.lower() not in valid_extensions:
        raise ValueError(
            f"Invalid target extension: {target_extension}. Must be one of {valid_extensions}"
        )

    # Construct the full image path
    image_path = os.path.join(images_folder, image_file_name)

    # Extract the current extension
    current_extension = os.path.splitext(image_file_name)[1][1:].lower()

    # Check if the current extension is valid
    if current_extension not in valid_extensions:
        raise ValueError(
            f"Invalid current extension: {current_extension}. Must be one of {valid_extensions}"
        )

    # If the current extension is the same as the target extension, do nothing
    if current_extension == target_extension.lower():
        print(f"The file is already in the {target_extension} format.")
        return image_file_name

    # Load the image
    image = PILImage.open(image_path)

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

    # Extract the filename without extension
    filename_without_extension = os.path.splitext(image_file_name)[0]

    # Define the output path
    output_file_name = f"{filename_without_extension}.{target_extension.lower()}"
    output_path = os.path.join(images_folder, output_file_name)

    # Save the image in the target format with the specified quality
    # if target_extension.lower() in {'jpg', 'jpeg'}:
    #     image.save(output_path, target_extension.upper(), quality=quality, optimize=True)
    # else:
    image.save(output_path, target_extension.lower(), quality=quality, optimize=True)

    print(
        f"Converted {image_path} to {output_path} with max width {max_width}, max height {max_height}, and quality {quality}"
    )
    return output_file_name
