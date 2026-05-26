from src.pipeline import run_pipeline

if __name__ == "__main__":
    run_pipeline(
        scrape=False,
        max_hotels_per_city=10,
        scrape_reviews=True,
        max_review_pages_per_hotel=4,
        max_scroll_rounds=1,
    )