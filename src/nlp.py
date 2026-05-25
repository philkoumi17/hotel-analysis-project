import spacy

# Load spaCy models
nlp_en = spacy.load("en_core_web_sm")
nlp_fr = spacy.load("fr_core_news_sm")

# English keywords
COMFORT_KEYWORDS_EN = [
    "comfortable",
    "bed",
    "quiet",
    "sleep",
    "clean",
    "spacious",
    "relaxing",
    "comfort",
]

SUSTAINABILITY_KEYWORDS_EN = [
    "eco",
    "sustainable",
    "green",
    "recycling",
    "environment",
    "energy",
]

# French keywords
COMFORT_KEYWORDS_FR = [
    "confortable",
    "calme",
    "silencieux",
    "lit",
    "propre",
    "reposant",
    "confort",
]

SUSTAINABILITY_KEYWORDS_FR = [
    "écologique",
    "durable",
    "recyclage",
    "environnement",
    "vert",
    "énergie",
]

def analyze_review_topics(text):

    if not text:
        return {
            "comfort_mentions": 0,
            "sustainability_mentions": 0,
        }

    text = text.lower()

    # Process text with both models
    doc_en = nlp_en(text)
    doc_fr = nlp_fr(text)

    comfort_count = 0
    sustainability_count = 0

    # English analysis
    for token in doc_en:

        if token.text in COMFORT_KEYWORDS_EN:
            comfort_count += 1

        if token.text in SUSTAINABILITY_KEYWORDS_EN:
            sustainability_count += 1

    # French analysis
    for token in doc_fr:

        if token.text in COMFORT_KEYWORDS_FR:
            comfort_count += 1

        if token.text in SUSTAINABILITY_KEYWORDS_FR:
            sustainability_count += 1

    return {
        "comfort_mentions": comfort_count,
        "sustainability_mentions": sustainability_count,
    }