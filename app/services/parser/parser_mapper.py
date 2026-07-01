from app.schemas.product import ProductCreate, ProductType, BookDetails


DEFAULT_LANGUAGE = "English"


def map_scraped_book_to_product(scraped_book: dict, category_id: str) -> ProductCreate:
    
    return ProductCreate(
        name=scraped_book["name"],
        description=scraped_book.get("description", "")[:1000] or "No description available.",
        price=scraped_book["price"],
        stock_quantity=scraped_book["stock_quantity"],
        category_id=category_id,
        product_type=ProductType.BOOK,
        book_details=BookDetails(
            language=DEFAULT_LANGUAGE,
            upc=scraped_book.get("upc"),
            rating=scraped_book.get("rating"),
            image_url=scraped_book.get("image_url"),
            source_url=scraped_book.get("url"),
        ),
    )