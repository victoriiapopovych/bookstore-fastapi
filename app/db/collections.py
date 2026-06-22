from app.db import mongodb


def get_category_collection():
    return mongodb.database["categories"]