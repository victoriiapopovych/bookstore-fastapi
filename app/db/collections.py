from app.db import mongodb


def get_category_collection():
    return mongodb.database["categories"]


def get_author_collection():
    return mongodb.database["authors"]


def get_product_collection():
    return mongodb.database["products"]