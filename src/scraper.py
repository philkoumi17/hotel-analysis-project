import json
import random
from pathlib import Path
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright
from src.utils import get_dates, random_delay, simulate_human_mouse

BASE_DIR = Path(__file__).resolve().parents[1]
USER_AGENTS_PATH = BASE_DIR / "config" / "user_agents.json"

with open(USER_AGENTS_PATH, "r", encoding="utf-8") as f:
    USER_AGENTS = json.load(f)

def dismiss_login_popup(page):
    selectors = [
        '//button[contains(@aria-label,"Ignorer")]',
        '//button[contains(@aria-label,"Dismiss")]',
        '//button[contains(@aria-label,"Fermer")]',
        '//button[contains(text(),"Dismiss")]',
        '//button[contains(text(),"Fermer")]',
        '//button[contains(text(),"Accept")]',
        '//button[contains(text(),"Accepter")]',
        '//button[contains(text(),"J’accepte")]',
        'button[aria-label*="Dismiss"]',
        'button[aria-label*="Fermer"]',
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector).first

            if locator.count() > 0 and locator.is_visible():
                locator.click(timeout=2000)
                random_delay(1, 2)
                return True

        except Exception:
            pass

    try:
        page.keyboard.press("Escape")
        random_delay(0.5, 1)
    except Exception:
        pass

    return False

def safe_click(page, selectors, timeout=10000):
    dismiss_login_popup(page)

    for selector in selectors:
        try:
            locator = page.locator(selector).first

            if locator.count() > 0:
                locator.wait_for(state="visible", timeout=timeout)
                locator.click(timeout=timeout, force=True)
                return True

        except Exception:
            continue

    return False

def visit_booking_homepage(p):
    browser_name = random.choice(["firefox", "chromium"])
    user_agent = random.choice(USER_AGENTS[browser_name])

    print(f"Using browser: {browser_name}")

    browser = getattr(p, browser_name).launch(headless=False)

    context = browser.new_context(
        user_agent=user_agent,
        viewport={"width": 1280, "height": 800},
        locale="fr-FR",
        extra_http_headers={
            "Accept-Language": "fr-FR,fr;q=0.9",
        },
    )

    context.clear_cookies()

    context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    page = context.new_page()

    page.goto(
        "https://www.booking.com/?lang=fr",
        wait_until="domcontentloaded",
        timeout=60000,
    )

    random_delay(2, 4)
    dismiss_login_popup(page)

    return page, context, browser

def search_booking_homepage(page, city_name):
    tomorrow, day_after = get_dates()

    try:
        page.wait_for_selector('input[name="ss"]', timeout=20000)

        page.fill('input[name="ss"]', "")
        page.type('input[name="ss"]', city_name, delay=random.randint(50, 150))

        print(f"Entered city: {city_name}")

        random_delay(1, 2)
        dismiss_login_popup(page)

        date_clicked = safe_click(
            page,
            [
                '[data-testid="searchbox-dates-container"]',
                '[data-testid="date-display-field-start"]',
                'button[data-testid="searchbox-dates-container"]',
                'div[data-testid="searchbox-dates-container"]',
                'button:has-text("Arrivée")',
                'button:has-text("Date d’arrivée")',
                'button:has-text("Date d’arrivée ")',
                'button:has-text("Check-in")',
            ],
        )

        if not date_clicked:
            raise Exception("Date picker not found")

        random_delay(1, 2)

        if not safe_click(
            page,
            [
                f"//span[@data-date='{tomorrow}']",
                f"button[data-date='{tomorrow}']",
                f"td[data-date='{tomorrow}']",
                f"//button[@data-date='{tomorrow}']",
            ],
        ):
            raise Exception("Check-in date not found")

        if not safe_click(
            page,
            [
                f"//span[@data-date='{day_after}']",
                f"button[data-date='{day_after}']",
                f"td[data-date='{day_after}']",
                f"//button[@data-date='{day_after}']",
            ],
        ):
            raise Exception("Check-out date not found")

        simulate_human_mouse(page)

        if not safe_click(
            page,
            [
                "button[type='submit']",
                'button:has-text("Rechercher")',
                'button:has-text("Search")',
            ],
        ):
            raise Exception("Search button not found")

        print("Search button clicked.")
        random_delay(5, 7)

    except Exception as e:
        print(f"Normal search failed: {e}")
        print("Using direct search URL fallback...")

        encoded_city = quote_plus(city_name)

        search_url = (
            "https://www.booking.com/searchresults.fr.html"
            f"?ss={encoded_city}"
            f"&checkin={tomorrow}"
            f"&checkout={day_after}"
            "&group_adults=2"
            "&no_rooms=1"
            "&group_children=0"
            "&selected_currency=EUR"
        )

        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)

        random_delay(5, 7)
        dismiss_login_popup(page)

    try:
        page.wait_for_selector(
            '[data-testid="property-card"], div[data-results-container="1"]',
            timeout=30000,
        )
        print("Search results loaded.")

    except Exception:
        print("Warning: results container not confirmed, continuing anyway.")

def find_load_more_button(page):
    selectors = [
        "button:has-text('Afficher plus de résultats')",
        "button:has-text('Load more results')",
        "//button[.//span[contains(text(),'Afficher plus de résultats')]]",
        "//button[.//span[contains(text(),'Load more results')]]",
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector).first

            if locator.count() > 0 and locator.is_visible():
                return locator

        except Exception:
            pass

    return None

def scroll_and_load_all_results(page, max_rounds=20):
    last_height = 0
    stagnant_rounds = 0

    for round_num in range(1, max_rounds + 1):
        print(f"Scroll round {round_num}/{max_rounds}")

        try:
            dismiss_login_popup(page)

            for _ in range(4):
                page.mouse.wheel(0, random.randint(1500, 2500))
                random_delay(1, 2)

            load_more_btn = find_load_more_button(page)

            if load_more_btn:
                try:
                    load_more_btn.scroll_into_view_if_needed()
                    random_delay(1, 2)
                    load_more_btn.click(force=True)
                    random_delay(3, 5)

                except Exception as e:
                    print(f"Load more click failed: {e}")

            new_height = page.evaluate("document.body.scrollHeight")

            if new_height == last_height:
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0
                last_height = new_height

            if stagnant_rounds >= 3:
                break

        except Exception as e:
            print(f"Scroll error: {e}")
            break

def booking_list_scraping(
    city_name,
    output_file,
    max_scroll_rounds=20,
):
    with sync_playwright() as p:
        page, context, browser = visit_booking_homepage(p)

        try:
            search_booking_homepage(page, city_name)

            scroll_and_load_all_results(
                page,
                max_rounds=max_scroll_rounds,
            )

            html = page.content()

            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"Saved HTML: {output_path}")

        finally:
            context.close()
            browser.close()