import json
import random
from pathlib import Path

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
    page.goto("https://www.booking.com/?lang=fr", wait_until="domcontentloaded")

    random_delay(2, 4)
    dismiss_login_popup(page)

    return page, context, browser

def search_booking_homepage(page, city_name):
    page.wait_for_selector('input[name="ss"]', timeout=20000)

    page.fill('input[name="ss"]', "")
    page.type('input[name="ss"]', city_name, delay=random.randint(50, 150))

    random_delay(1, 2)

    if not safe_click(
        page,
        [
            '[data-testid="searchbox-dates-container"]',
            '[data-testid="date-display-field-start"]',
        ],
    ):
        raise Exception("Date picker not found")

    tomorrow, day_after = get_dates()

    if not safe_click(
        page,
        [
            f"//span[@data-date='{tomorrow}']",
            f"button[data-date='{tomorrow}']",
        ],
    ):
        raise Exception("Check-in date not found")

    if not safe_click(
        page,
        [
            f"//span[@data-date='{day_after}']",
            f"button[data-date='{day_after}']",
        ],
    ):
        raise Exception("Check-out date not found")

    simulate_human_mouse(page)

    if not safe_click(
        page,
        [
            "button[type='submit']",
            'button:has-text("Rechercher")',
        ],
    ):
        raise Exception("Search button not found")

    random_delay(5, 7)

def find_load_more_button(page):
    selectors = [
        "button:has-text('Afficher plus de résultats')",
        "button:has-text('Load more results')",
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

    for _ in range(max_rounds):
        try:
            dismiss_login_popup(page)

            for _ in range(4):
                page.mouse.wheel(0, random.randint(1500, 2500))
                random_delay(1, 2)

            load_more_btn = find_load_more_button(page)

            if load_more_btn:
                try:
                    load_more_btn.scroll_into_view_if_needed()
                    load_more_btn.click(force=True)
                    random_delay(3, 5)
                except Exception:
                    pass

            new_height = page.evaluate("document.body.scrollHeight")

            if new_height == last_height:
                stagnant_rounds += 1
            else:
                stagnant_rounds = 0
                last_height = new_height

            if stagnant_rounds >= 3:
                break

        except Exception:
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
            scroll_and_load_all_results(page, max_scroll_rounds)

            html = page.content()

            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)

        finally:
            context.close()
            browser.close()