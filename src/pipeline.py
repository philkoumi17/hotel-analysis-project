import csv
import json
import re
from pathlib import Path

import pandas as pd

from src.scraper import booking_list_scraping
from src.parser import extract_hotel_data
from src.review_scraper import scrape_reviews_for_hotels
from src.utils import safe_filename

BASE_DIR = Path(__file__).resolve().parents[1]

CITIES_FILE = BASE_DIR / "config" / "cities.txt"

RAW_HTML_DIR = BASE_DIR / "data" / "raw_html"
JSON_DIR = BASE_DIR / "data" / "json"
CSV_DIR = BASE_DIR / "data" / "csv"

def create_directories():
    RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)
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

    value = value.replace("\r\n", " ")
    value = value.replace("\n", " ")
    value = value.replace("\r", " ")

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
    hotels_rows = []
    reviews_rows = []

    # ==========================================
    # HOTELS CSV
    # ==========================================

    for hotel_id, hotel in enumerate(all_hotels, start=1):
        hotels_rows.append(
            {
                "hotel_id": hotel_id,
                "city": hotel.get("city"),
                "title": hotel.get("title"),
                "price": hotel.get("price"),
                "booking_url": hotel.get("booking_url"),
                "star_rating": hotel.get("star_rating"),
                "review_score": hotel.get("review_score"),
                "review_count": hotel.get("review_count"),
                "review_scraping_status": hotel.get(
                    "review_scraping_status"
                ),
                "img_src": hotel.get("img_src"),
                "img_alt": hotel.get("img_alt"),
            }
        )

        # ==========================================
        # REVIEWS CSV
        # ==========================================

        reviews = hotel.get("reviews", [])

        for review in reviews:
            reviews_rows.append(
                {
                    "hotel_id": hotel_id,
                    "hotel_title": hotel.get("title"),
                    "city": hotel.get("city"),

                    "reviewer_name":
                        review.get("reviewer_name"),

                    "reviewer_country":
                        review.get("reviewer_country"),

                    "review_title":
                        review.get("review_title"),

                    "review_positive":
                        review.get("review_positive"),

                    "review_negative":
                        review.get("review_negative"),

                    "review_date":
                        review.get("review_date"),

                    "review_score":
                        review.get("review_card_score"),

                    "full_review_text":
                        review.get("full_review_text"),
                }
            )

    # ==========================================
    # DATAFRAMES
    # ==========================================

    hotels_df = pd.DataFrame(hotels_rows)
    reviews_df = pd.DataFrame(reviews_rows)

    # ==========================================
    # CLEAN TEXT
    # ==========================================

    for col in hotels_df.columns:
        hotels_df[col] = hotels_df[col].map(clean_for_ssis)

    for col in reviews_df.columns:
        reviews_df[col] = reviews_df[col].map(clean_for_ssis)

    # ==========================================
    # SAVE HOTELS CSV
    # ==========================================

    hotels_output = CSV_DIR / "booking_hotels.csv"

    hotels_df.to_csv(
        hotels_output,
        index=False,
        encoding="utf-8-sig",
        sep=",",
        quoting=csv.QUOTE_ALL,
        lineterminator="\r\n",
    )

    # ==========================================
    # SAVE REVIEWS CSV
    # ==========================================

    reviews_output = CSV_DIR / "booking_reviews.csv"

    reviews_df.to_csv(
        reviews_output,
        index=False,
        encoding="utf-8-sig",
        sep=",",
        quoting=csv.QUOTE_ALL,
        lineterminator="\r\n",
    )

    print(f"\nSaved hotels CSV: {hotels_output}")
    print(f"Total hotels: {len(hotels_df)}")

    print(f"\nSaved reviews CSV: {reviews_output}")
    print(f"Total reviews: {len(reviews_df)}")

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

        html_path = RAW_HTML_DIR / f"{city_file_name}.html"

        # ==========================================
        # SCRAPE HOTEL LIST
        # ==========================================

        if scrape:
            booking_list_scraping(
                city_name=city,
                output_file=str(html_path),
                max_scroll_rounds=max_scroll_rounds,
            )

        else:
            print(f"Skipping scraping. Using existing HTML: {html_path}")

        # ==========================================
        # EXTRACT HOTELS
        # ==========================================

        hotels = extract_hotel_data(
            file_path=str(html_path),
            city_name=city,
            max_hotels=max_hotels_per_city,
        )

        # ==========================================
        # SCRAPE REVIEWS
        # ==========================================

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