from core.database import Base, engine, SessionLocal
from populate_db.user_restaurants import populate_users, populate_restaurants
from populate_db.populate_database_functions import restaurant_content
from populate_db.populate_new_restaurants import new_restaurant_content


def populate_database():
    try:
        with SessionLocal() as db:
            print("DB POPULATE")

            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)

            users = populate_users(db, "./populate_db/users.json")
            new_user = users.get("ignacio.albornoz@ug.uchile.cl")
            fabian_user = users.get("fabian.issi.19@gmail.com")
            new_user_2 = users.get("ignacioalbornoz001@gmail.com")
            fabian_user_2 = users.get("fabian.issi@ug.uchile.cl")

            restaurants = populate_restaurants(
                db,
                users,
                "./populate_db/restaurants.json",
                "./populate_db/user_restaurants_roles.json",
            )

            for _, new_restaurant in restaurants.items():
                restaurant_content(
                    new_restaurant, new_user, fabian_user, new_user_2, fabian_user_2, db
                )

            new_restaurants = populate_restaurants(
                db,
                users,
                "./populate_db/new_restaurants.json",
                "./populate_db/new_user_restaurants_roles.json",
            )

            for _, new_restaurant in new_restaurants.items():
                new_restaurant_content(
                    new_restaurant, new_user, fabian_user, new_user_2, fabian_user_2, db
                )

            print("Base de datos poblada con éxito")

    except Exception as e:
        print("DB ROLLBACK")
        db.rollback()
        print(f"Error: {e}")
