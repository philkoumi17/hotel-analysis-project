import csv
import json
import re
from pathlib import Path

import pandas as pd

from src.scraper import booking_list_scraping
from src.parser import extract_hotel_data
from src.review_scraper import scrape_reviews_for_hotels
from src.utils import safe_filename
from src.nlp import analyze_review_topics

BASE_DIR = Path(__file__).resolve().parents[1]

CITIES_FILE = BASE_DIR / "config" / "cities.txt"

HTML_DIR = BASE_DIR / "data" / "raw_html"
JSON_DIR = BASE_DIR / "data" / "json"
CSV_DIR = BASE_DIR / "data" / "csv"

def create_directories():
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    JSON_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)

def load_cities():
    with open(CITIES_FILE, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]

def clean_for_ssis(value):
    if value is None:
        return ""

    value = str(value)

    value = value.replace("\r\n", " | ")
    value = value.replace("\n", " | ")
    value = value.replace("\r", " | ")

    value = value.replace(";", " ")
    value = value.replace(",", " ")
    value = value.replace('"', " ")

    value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value

def save_city_json(city_name, hotels):
    city_file_name = safe_filename(city_name)
    output_path = JSON_DIR / f"{city_file_name}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(hotels, f, ensure_ascii=False, indent=2)

    print(f"Saved JSON for {city_name}: {output_path}")

def save_final_json(all_hotels):
    output_path = JSON_DIR / "booking_hotels_all_cities.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_hotels, f, ensure_ascii=False, indent=2)

    print(f"Saved final JSON: {output_path}")

def save_final_csv(all_hotels):
    rows = []

    for hotel in all_hotels:
        nlp_result = analyze_review_topics(
            hotel.get("reviews_text", "")
        )
        rows.append(
            {
                "city": hotel.get("city"),
                "title": hotel.get("title"),
                "price": hotel.get("price"),
                "booking_url": hotel.get("booking_url"),
                "star_rating": hotel.get("star_rating"),
                "review_score": hotel.get("review_score"),
                "review_count": hotel.get("review_count"),
                "review_scraping_status": hotel.get("review_scraping_status"),
                "reviews_text": hotel.get("reviews_text"),
                "reviews_positive_text": hotel.get("reviews_positive_text"),
                "reviews_negative_text": hotel.get("reviews_negative_text"),
                "img_src": hotel.get("img_src"),
                "img_alt": hotel.get("img_alt"),
                "comfort_mentions": nlp_result["comfort_mentions"],
                "sustainability_mentions": nlp_result["sustainability_mentions"],
            }
        )

    df = pd.DataFrame(rows)

    columns_order = [
        "city",
        "title",
        "price",
        "booking_url",
        "star_rating",
        "review_score",
        "review_count",
        "review_scraping_status",
        "reviews_text",
        "reviews_positive_text",
        "reviews_negative_text",
        "img_src",
        "img_alt",
        "comfort_mentions",
        "sustainability_mentions",
    ]

    df = df.reindex(columns=columns_order)

    # Clean all fields so SSIS does not break rows
    df = df.apply(lambda col: col.map(clean_for_ssis))

    output_path = CSV_DIR / "booking_hotels_all_cities.csv"

    # SSIS-friendly CSV
    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
        sep=";",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\r\n",
    )

    print(f"\nSaved final CSV: {output_path}")
    print(f"Total hotels: {len(df)}")

def run_pipeline(
    scrape=True,
    max_hotels_per_city=None,
    scrape_reviews=False,
    max_review_pages_per_hotel=1,
    max_scroll_rounds=20,
):
    create_directories()

    cities = load_cities()
    all_hotels = []

    for city in cities:
        print("\n==============================")
        print(f"Processing city: {city}")
        print("==============================")

        city_file_name = safe_filename(city)
        html_path = HTML_DIR / f"{city_file_name}.html"

        if scrape:
            booking_list_scraping(
                city_name=city,
                output_file=str(html_path),
                max_scroll_rounds=max_scroll_rounds,
            )
        else:
            print(f"Skipping scraping. Using existing HTML: {html_path}")

        hotels = extract_hotel_data(
            file_path=str(html_path),
            city_name=city,
            max_hotels=max_hotels_per_city,
        )

        if scrape_reviews:
            print(
                f"Scraping reviews for {city} "
                f"(max {max_review_pages_per_hotel} pages/hotel)"
            )

            hotels = scrape_reviews_for_hotels(
                hotels=hotels,
                max_pages_per_hotel=max_review_pages_per_hotel,
            )

        save_city_json(city, hotels)
        all_hotels.extend(hotels)

    save_final_json(all_hotels)
    save_final_csv(all_hotels)