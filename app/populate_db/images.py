from shared_models.images import Image


def populate_default_image(db):
    default_image = Image(real_name="default.png", path_name="default.png")
    db.add(default_image)
    db.commit()
