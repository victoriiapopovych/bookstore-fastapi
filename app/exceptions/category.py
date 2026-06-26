class CategoryNotFoundError(Exception):
    pass


class InvalidCategoryIdError(Exception):
    pass


class InvalidParentCategoryError(Exception):
    pass


class CategorySlugAlreadyExistsError(Exception):
    pass