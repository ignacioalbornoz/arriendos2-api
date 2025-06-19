import json
from sqlalchemy.exc import IntegrityError
from shared_models.oneclick_cards import OneClickCard


def load_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def populate_oneclick_cards(db, users, file_path):
    data = load_data(file_path)
    cards = data["oneclick_cards"]
    print(users)
    for card_info in cards:
        print(card_info["owner_email"])
        user = users.get(card_info["owner_email"])
        print(user)
        new_card = OneClickCard(
            user_id=user.id,
            card_type=card_info["card_type"],
            card_number=card_info["card_number"],
        )
        db.add(new_card)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        print(f"Failed to commit changes: {str(e)}")
