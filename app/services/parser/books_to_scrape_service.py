import logging
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.exceptions.parser import ExternalPageNotFoundError, ExternalSiteUnavailableError, InvalidParserUrlError, NoBooksFoundError


logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com/"

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


async def fetch_page(url: str) -> str:
    if not url.startswith(BASE_URL):
        raise InvalidParserUrlError

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise ExternalPageNotFoundError from exc

        raise ExternalSiteUnavailableError from exc

    except httpx.RequestError as exc:
        raise ExternalSiteUnavailableError from exc


def parse_price(price_text: str) -> float:
    return float(price_text.replace("£", "").strip())


def parse_rating(element) -> int | None:
    if not element:
        return None

    for class_name in element.get("class", []):
        if class_name in RATING_MAP:
            return RATING_MAP[class_name]

    return None


def parse_stock_quantity(stock_text: str) -> int:
    match = re.search(r"\d+", stock_text)
    return int(match.group()) if match else 0


async def get_available_categories():
    html = await fetch_page(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")

    categories = []

    for link in soup.select(".side_categories ul li ul li a"):
        name = link.text.strip()
        href = link.get("href")

        if not name or not href:
            continue

        categories.append(
            {
                "name": name,
                "url": urljoin(BASE_URL, href),
            }
        )

    if not categories:
        raise NoBooksFoundError

    logger.info("Parsed categories: %s", len(categories))
    return categories


async def get_books_from_category(
    category_url: str,
    limit: int | None = None,
):
    html = await fetch_page(category_url)
    soup = BeautifulSoup(html, "html.parser")

    books = []

    for book_card in soup.select("article.product_pod"):
        title_element = book_card.select_one("h3 a")
        price_element = book_card.select_one(".price_color")
        image_element = book_card.select_one(".image_container img")
        rating_element = book_card.select_one("p.star-rating")

        if not title_element or not price_element:
            continue

        book_url = urljoin(category_url, title_element.get("href"))
        image_url = (
            urljoin(category_url, image_element.get("src"))
            if image_element
            else None
        )

        books.append(
            {
                "name": title_element.get("title"),
                "price": parse_price(price_element.text),
                "rating": parse_rating(rating_element),
                "url": book_url,
                "image_url": image_url,
            }
        )

        if limit and len(books) >= limit:
            break

    if not books:
        raise NoBooksFoundError

    logger.info(
        "Parsed books from category: url=%s, count=%s",
        category_url,
        len(books),
    )

    return books


async def get_book_details(book_url: str):
    html = await fetch_page(book_url)
    soup = BeautifulSoup(html, "html.parser")

    description_element = soup.select_one("#product_description + p")
    description = description_element.text.strip() if description_element else ""

    product_info = {}

    for row in soup.select("table.table.table-striped tr"):
        key_element = row.select_one("th")
        value_element = row.select_one("td")

        if key_element and value_element:
            product_info[key_element.text.strip()] = value_element.text.strip()

    details = {
        "upc": product_info.get("UPC"),
        "description": description,
        "stock_quantity": parse_stock_quantity(
            product_info.get("Availability", "")
        ),
    }

    if not details["upc"]:
        raise ExternalPageNotFoundError

    logger.info("Parsed book details: url=%s, upc=%s", book_url, details["upc"])
    return details


async def get_full_books_from_category(
    category_url: str,
    limit: int | None = None,
):
    books = await get_books_from_category(
        category_url=category_url,
        limit=limit,
    )

    full_books = []

    for book in books:
        details = await get_book_details(book["url"])
        full_books.append({**book, **details})

    logger.info(
        "Parsed full books from category: url=%s, count=%s",
        category_url,
        len(full_books),
    )

    return full_books


async def get_full_book_by_url(book_url: str):
    html = await fetch_page(book_url)
    soup = BeautifulSoup(html, "html.parser")

    title_element = soup.select_one(".product_main h1")
    price_element = soup.select_one(".product_main .price_color")
    image_element = soup.select_one(".item.active img")
    rating_element = soup.select_one(".product_main p.star-rating")

    if not title_element or not price_element:
        raise ExternalPageNotFoundError

    details = await get_book_details(book_url)

    book = {
        "name": title_element.text.strip(),
        "price": parse_price(price_element.text),
        "rating": parse_rating(rating_element),
        "url": book_url,
        "image_url": (
            urljoin(book_url, image_element.get("src"))
            if image_element
            else None
        ),
        **details,
    }

    logger.info("Parsed full book: url=%s, upc=%s", book_url, book["upc"])

    return book