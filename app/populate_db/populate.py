

import os

FILE_EXTENSION = os.getenv("FILE_EXTENSION")


# def populate_database(populate_images_flag=True):
#     try:
#         with SessionLocal() as db:
#             print("DB POPULATE")
#             Base.metadata.drop_all(bind=engine)
#             Base.metadata.create_all(bind=engine)
#             print("Populate permissions")
#             populate_permissions(db)
#             print("Populate Images")
#             populate_default_image(db)
#             # First create the users:
#             print("Populate Users")
#             users = populate_users(db, "./populate_db/users.json")
#             print("Populate supabase test Users")
#             test_users_supabase_setup()
#             print("Populate Restaurant")

#             MODE = os.getenv("MODE")
#             if MODE is None:
#                 raise EnvironmentError("The environment variable MODE is not defined.")
#             if MODE == "DEV":
#                 populate_restaurant(
#                     db,
#                     users,
#                     "./populate_db/test_restaurant/restaurant.json",
#                     "./populate_db/test_restaurant/user_restaurant_roles.json",
#                     "./populate_db/test_restaurant/restaurant_financial.json",
#                     "./populate_db/test_restaurant/menu.csv",
#                     "./populate_db/test_restaurant/category_images.csv",
#                     "./populate_db/test_restaurant/ImagesToAdd",
#                     FILE_EXTENSION,
#                     populate_images_flag,
#                 )
#             else:
#                 print("No fue necesario poblar test restaurant en modo producción")

#             populate_restaurant(
#                 db,
#                 users,
#                 "./populate_db/buen_sabor/restaurant.json",
#                 "./populate_db/buen_sabor/user_restaurant_roles.json",
#                 "./populate_db/buen_sabor/restaurant_financial.json",
#                 "./populate_db/buen_sabor/menu.csv",
#                 "./populate_db/buen_sabor/category_images.csv",
#                 "./populate_db/buen_sabor/ImagesToAdd",
#                 FILE_EXTENSION,
#                 populate_images_flag,
#             )
#             populate_restaurant(
#                 db,
#                 users,
#                 "./populate_db/cafe_noruega/restaurant.json",
#                 "./populate_db/cafe_noruega/user_restaurant_roles.json",
#                 "./populate_db/cafe_noruega/restaurant_financial.json",
#                 "./populate_db/cafe_noruega/menu.csv",
#                 "./populate_db/cafe_noruega/category_images.csv",
#                 "./populate_db/cafe_noruega/ImagesToAdd",
#                 FILE_EXTENSION,
#                 populate_images_flag,
#             )
#             print("Base de datos poblada con éxito")

#     except Exception as e:
#         print("DB ROLLBACK")
#         db.rollback()
#         print(f"Error: {e}")
