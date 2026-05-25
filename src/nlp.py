import spacy

nlp = spacy.load("en_core_web_sm")

COMFORT_KEYWORDS = [
    "comfortable",
    "bed",
    "quiet",
    "sleep",
    "clean",
    "spacious",
    "relaxing",
    "comfort",
]

SUSTAINABILITY_KEYWORDS = [
    "eco",
    "sustainable",
    "green",
    "recycling",
    "environment",
    "energy",
]

def analyze_review_topics(text):

    if not text:
        return {
            "comfort_mentions": 0,
            "sustainability_mentions": 0,
        }

    doc = nlp(text.lower())

    comfort_count = 0
    sustainability_count = 0

    for token in doc:

        if token.text in COMFORT_KEYWORDS:
            comfort_count += 1

        if token.text in SUSTAINABILITY_KEYWORDS:
            sustainability_count += 1

    return {
        "comfort_mentions": comfort_count,
        "sustainability_mentions": sustainability_count,
    }