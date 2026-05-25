from src.pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline(
        scrape=True,
        max_hotels_per_city=1,
        scrape_reviews=True,
        max_review_pages_per_hotel=1,
        max_scroll_rounds=1,
    )