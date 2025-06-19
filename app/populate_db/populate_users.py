import json


def load_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


# def create_user(db, user_info):
#     user = User(
#         display_name=user_info["display_name"],
#         email=user_info["email"],
#         phone_number=user_info.get(
#             "phone_number"
#         ),  # Using get to handle missing phone_number
#         premium=user_info.get("premium", False),
#         terms_accepted=user_info.get("terms_accepted", False),
#     )
#     db.add(user)
#     return user


# def create_google_user(db, google_user_info, user_id):
#     google_user = GoogleUser(
#         id=google_user_info["id"],
#         user_id=user_id,
#         email=google_user_info["email"],
#         family_name=google_user_info["family_name"],
#         given_name=google_user_info["given_name"],
#         hd=google_user_info.get("hd"),  # Handle optional domain
#         name=google_user_info["name"],
#         locale=google_user_info["locale"],
#         verified_email=google_user_info["verified_email"],
#     )
#     db.add(google_user)


# def populate_users(db, data_path):
#     user_data = load_data(data_path)
#     users = {}
#     try:
#         for user_info in user_data["users"]:
#             new_user = create_user(db, user_info)
#             users[new_user.email] = new_user
#             db.commit()  # Committing here ensures user_id is generated

#             # create_google_user(db, user_info["google_info"], new_user.id)
#             db.commit()  # Commit changes after both user and GoogleUser are added

#     except Exception as e:
#         db.rollback()  # Rollback in case of any failure
#         print(f"Error occurred: {e}")

#     return users  # Return the loaded data for any further processing or validation
