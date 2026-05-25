from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

BASE_URL = "https://www.booking.com"

def clean_text(value):
    if not value:
        return ""
    return " ".join(value.get_text(" ", strip=True).split())

def clean_string(value):
    if not value:
        return ""
    return " ".join(str(value).split())

def get_first_text(parent, selectors):
    for selector in selectors:
        element = parent.select_one(selector)
        if element:
            text = clean_text(element)
            if text:
                return text
    return ""

def get_first_attr(parent, selectors, attr):
    for selector in selectors:
        element = parent.select_one(selector)
        if element and element.get(attr):
            return clean_string(element.get(attr))

    return ""

def extract_hotel_data(file_path: str, city_name: str, max_hotels=None):
    html_path = Path(file_path)

    if not html_path.exists():
        print(f"HTML file not found: {html_path}")
        return []

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    cards = soup.select('[data-testid="property-card"]')

    if not cards:
        cards = soup.select("div[data-testid]")

    hotels = []

    for card in cards:
        title = get_first_text(
            card,
            [
                '[data-testid="title"]',
                'div[data-testid="title"]',
                "h3",
            ],
        )

        if not title:
            continue

        booking_url = get_first_attr(
            card,
            [
                'a[data-testid="title-link"]',
                'a[href*="/hotel/"]',
            ],
            "href",
        )

        if booking_url:
            booking_url = urljoin(BASE_URL, booking_url)

        price = get_first_text(
            card,
            [
                '[data-testid="price-and-discounted-price"]',
                '[data-testid="price-for-x-nights"]',
                'span[data-testid="price-and-discounted-price"]',
            ],
        )

        review_score = get_first_text(
            card,
            [
                '[data-testid="review-score"]',
                '[aria-label*="Scored"]',
                '[aria-label*="Note"]',
            ],
        )

        review_count = get_first_text(
            card,
            [
                '[data-testid="review-score"] + div',
                '[class*="review"]',
            ],
        )

        star_rating = get_first_attr(
            card,
            [
                '[data-testid="rating-stars"]',
                '[aria-label*="étoile"]',
                '[aria-label*="star"]',
            ],
            "aria-label",
        )

        img_src = get_first_attr(
            card,
            [
                'img[data-testid="image"]',
                "img",
            ],
            "src",
        )

        img_alt = get_first_attr(
            card,
            [
                'img[data-testid="image"]',
                "img",
            ],
            "alt",
        )

        hotels.append(
            {
                "city": city_name,
                "title": title,
                "price": price,
                "booking_url": booking_url,
                "star_rating": star_rating,
                "review_score": review_score,
                "review_count": review_count,
                "review_scraping_status": "not_processed",
                "reviews_text": "",
                "reviews_positive_text": "",
                "reviews_negative_text": "",
                "img_src": img_src,
                "img_alt": img_alt,
            }
        )

        if max_hotels and len(hotels) >= max_hotels:
            break

    print(f"Extracted {len(hotels)} hotels from {html_path}")

    return hotels