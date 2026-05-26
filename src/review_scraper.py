import random
import time

from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

def random_delay(a=1.0, b=2.0):
    time.sleep(random.uniform(a, b))

def safe_text(locator):
    try:
        if locator.count() > 0:
            return locator.first.inner_text().strip()
    except Exception:
        pass

    return ""

def dismiss_popups(page):
    selectors = [
        'button[aria-label*="Dismiss"]',
        'button[aria-label*="Fermer"]',
        'button:has-text("Dismiss")',
        'button:has-text("Fermer")',
        'button:has-text("Accept")',
        'button:has-text("Accepter")',
        'button:has-text("J’accepte")',
    ]

    for sel in selectors:
        try:
            btn = page.locator(sel).first

            if btn.count() > 0 and btn.is_visible():
                btn.click(timeout=2000)
                print(f"Popup handled with selector: {sel}")
                random_delay(1, 1.5)
                return

        except Exception:
            pass

def try_click_reviews(page, hotel_title: str) -> bool:
    selectors = [
        'a[rel="reviews"]',
        'a[href="#blockdisplay4"]',
        'a:has([data-testid="review-score-right-component"])',
        '[data-testid="review-score-right-component"]',
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector).first

            if locator.count() > 0 and locator.is_visible():
                locator.scroll_into_view_if_needed()
                random_delay(0.8, 1.5)
                locator.click(timeout=5000)

                print(f"[{hotel_title}] Clicked reviews with selector: {selector}")
                return True

        except Exception as e:
            print(f"[{hotel_title}] Failed selector {selector}: {e}")

    print(f"[{hotel_title}] No reviews button found.")
    return False

def extract_review_cards_from_current_page(page, hotel_title: str):
    extracted = []

    card_selectors = [
        'div[data-testid="review-card"]',
        'div[data-testid="review-cards"] > div',
    ]

    cards = None

    for sel in card_selectors:
        try:
            loc = page.locator(sel)

            if loc.count() > 0:
                cards = loc
                print(
                    f"[{hotel_title}] Found review cards with selector: "
                    f"{sel} -> {loc.count()} cards"
                )
                break

        except Exception:
            pass

    if cards is None:
        print(f"[{hotel_title}] No review cards found on current page.")
        return extracted

    count = cards.count()

    for i in range(count):
        try:
            card = cards.nth(i)

            reviewer_name = ""
            reviewer_country = ""
            review_title = ""
            review_positive = ""
            review_negative = ""
            review_date = ""
            review_card_score = ""
            full_review_text = ""

            possible_name_selectors = [
                '[data-testid="reviewer-name"]',
                'div[class*="reviewer"]',
                'span[class*="reviewer"]',
            ]

            possible_country_selectors = [
                '[data-testid="reviewer-country"]',
                'div[class*="country"]',
                'span[class*="country"]',
            ]

            possible_title_selectors = [
                '[data-testid="review-title"]',
                'h3',
                'h4',
                'div[class*="title"]',
            ]

            possible_positive_selectors = [
                '[data-testid="review-positive-text"]',
                'div[class*="positive"]',
            ]

            possible_negative_selectors = [
                '[data-testid="review-negative-text"]',
                'div[class*="negative"]',
            ]

            possible_date_selectors = [
                '[data-testid="review-date"]',
                'span[class*="date"]',
                'div[class*="date"]',
            ]

            possible_score_selectors = [
                '[data-testid="review-score"]',
                'div[aria-label*="Scored"]',
                'div[class*="score"]',
            ]

            for sel in possible_name_selectors:
                reviewer_name = safe_text(card.locator(sel))
                if reviewer_name:
                    break

            for sel in possible_country_selectors:
                reviewer_country = safe_text(card.locator(sel))
                if reviewer_country:
                    break

            for sel in possible_title_selectors:
                review_title = safe_text(card.locator(sel))
                if review_title:
                    break

            for sel in possible_positive_selectors:
                review_positive = safe_text(card.locator(sel))
                if review_positive:
                    break

            for sel in possible_negative_selectors:
                review_negative = safe_text(card.locator(sel))
                if review_negative:
                    break

            for sel in possible_date_selectors:
                review_date = safe_text(card.locator(sel))
                if review_date:
                    break

            for sel in possible_score_selectors:
                review_card_score = safe_text(card.locator(sel))
                if review_card_score:
                    break

            try:
                full_review_text = card.inner_text().strip()
            except Exception:
                full_review_text = ""

            extracted.append(
                {
                    "reviewer_name": reviewer_name,
                    "reviewer_country": reviewer_country,
                    "review_title": review_title,
                    "review_positive": review_positive,
                    "review_negative": review_negative,
                    "review_date": review_date,
                    "review_card_score": review_card_score,
                    "full_review_text": full_review_text,
                }
            )

        except Exception as e:
            print(f"[{hotel_title}] Error extracting card {i}: {e}")

    return extracted

def scroll_reviews_popup(page, hotel_title: str):
    print(f"[{hotel_title}] Scrolling reviews area...")

    for _ in range(4):
        try:
            page.mouse.wheel(0, 2500)
            random_delay(1, 2)
        except Exception:
            pass

        try:
            container = page.locator('div[data-testid="review-cards"]').first

            if container.count() > 0:
                container.evaluate("(el) => el.scrollBy(0, el.scrollHeight)")
                random_delay(1, 2)

        except Exception:
            pass

def click_next_reviews_page(page, hotel_title: str) -> bool:
    next_selectors = [
        'button[aria-label="Page suivante"]',
        'button[aria-label="Next page"]',
        'button[aria-label*="suivante"]',
        'button[aria-label*="Next"]',
    ]

    for sel in next_selectors:
        try:
            btn = page.locator(sel).first

            if btn.count() > 0 and btn.is_visible() and btn.is_enabled():
                btn.scroll_into_view_if_needed()
                random_delay(0.5, 1)
                btn.click(timeout=5000)

                print(f"[{hotel_title}] Clicked next review page.")
                random_delay(2, 4)
                return True

        except Exception:
            pass

    print(f"[{hotel_title}] No next page button found.")
    return False

def extract_all_reviews_for_hotel(page, hotel_title: str, max_pages=5):
    all_reviews = []
    seen = set()

    for page_num in range(1, max_pages + 1):
        print(f"[{hotel_title}] Extracting review page {page_num}...")

        scroll_reviews_popup(page, hotel_title)

        current_reviews = extract_review_cards_from_current_page(
            page,
            hotel_title,
        )

        new_count = 0

        for review in current_reviews:
            key = review.get("full_review_text", "").strip()

            if key and key not in seen:
                seen.add(key)
                all_reviews.append(review)
                new_count += 1

        print(f"[{hotel_title}] Added {new_count} new reviews on page {page_num}")

        moved = click_next_reviews_page(page, hotel_title)

        if not moved:
            break

    return all_reviews

def scrape_reviews_for_hotels(
    hotels: list[dict],
    max_pages_per_hotel: int = 3,
) -> list[dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="fr-FR",
        )

        page = context.new_page()

        for idx, hotel in enumerate(hotels, start=1):
            title = hotel.get("title", "Unknown hotel")
            url = hotel.get("booking_url", "")

            print("\n" + "=" * 100)
            print(f"[{idx}] Processing reviews for hotel: {title}")

            hotel["reviews"] = []
            hotel["review_count"] = 0
            hotel["reviews_text"] = ""
            hotel["reviews_positive_text"] = ""
            hotel["reviews_negative_text"] = ""
            hotel["review_scraping_status"] = "not_processed"

            if not url:
                hotel["review_scraping_status"] = "missing_url"
                print(f"[{title}] Missing booking_url.")
                continue

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                random_delay(2, 4)
            except Exception as e:
                hotel["review_scraping_status"] = f"page_open_failed: {e}"
                print(f"[{title}] Failed to open page: {e}")
                continue

            dismiss_popups(page)

            clicked = try_click_reviews(page, title)

            if not clicked:
                hotel["review_scraping_status"] = "no_reviews_button"
                print(f"[{title}] No review section available.")
                continue

            try:
                page.wait_for_selector(
                    'div[data-testid="review-cards"]',
                    timeout=10000,
                )
                random_delay(2, 3)
            except PlaywrightTimeoutError:
                hotel["review_scraping_status"] = "review_popup_not_loaded"
                print(f"[{title}] Review popup/section did not load.")
                continue

            reviews = extract_all_reviews_for_hotel(
                page,
                title,
                max_pages=max_pages_per_hotel,
            )

            hotel["reviews"] = reviews
            hotel["review_count"] = len(reviews)
            hotel["reviews_text"] = " | ".join(
                r.get("full_review_text", "")
                for r in reviews
                if r.get("full_review_text")
            )
            hotel["reviews_positive_text"] = " | ".join(
                r.get("review_positive", "")
                for r in reviews
                if r.get("review_positive")
            )
            hotel["reviews_negative_text"] = " | ".join(
                r.get("review_negative", "")
                for r in reviews
                if r.get("review_negative")
            )

            hotel["review_scraping_status"] = (
                "success" if reviews else "no_reviews_found"
            )

            print(f"[{title}] Total reviews extracted: {len(reviews)}")

        context.close()
        browser.close()

    return hotels