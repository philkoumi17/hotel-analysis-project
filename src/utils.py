from datetime import datetime, timedelta
import random
import time
import re

def random_delay(min_sec=2, max_sec=4):
    time.sleep(random.uniform(min_sec, max_sec))

def simulate_human_mouse(page):
    viewport = page.viewport_size

    if not viewport:
        return

    width = viewport["width"]
    height = viewport["height"]

    for _ in range(random.randint(3, 4)):
        x = random.randint(0, width)
        y = random.randint(0, height)

        page.mouse.move(x, y, steps=random.randint(5, 10))
        time.sleep(random.uniform(0.2, 0.8))

def get_dates():
    today = datetime.now()

    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)

    return (
        tomorrow.strftime("%Y-%m-%d"),
        day_after_tomorrow.strftime("%Y-%m-%d"),
    )

def safe_filename(text: str):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")