"""
Natural Language Processing Service.
Handles translation, token-based deduplication, extractive summarization, and sentiment analysis.
Extracted faithfully from app.py without altering rules, stopwords, or thresholds.
"""

import re
from deep_translator import GoogleTranslator


def translate_to_target_lang(text: str, target_lang: str) -> str:
    """
    Translates input text to a target language code.
    If already English and standard ASCII, skips translation.
    Catches errors gracefully and returns the original text on failure.
    """
    if not text or not text.strip():
        return text
    try:
        if target_lang == 'en':
            if any(ord(char) > 127 for char in text):
                return GoogleTranslator(source='auto', target='en').translate(text)
            return text
        else:
            return GoogleTranslator(source='auto', target=target_lang).translate(text)
    except Exception:
        pass
    return text


def is_similar_to_existing(title: str, existing_titles: set | list, threshold: float = 0.45) -> bool:
    """
    Jaccard similarity de-duplicator helper.
    Tokenizes text, discards common stopwords, and compares intersection over union.
    """
    if not title or not title.strip():
        return False

    def clean_and_tokenize(text: str) -> set:
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "with", "is", "are", "was", "were", "of", "by", "that", "this",
            "these", "those", "it", "its", "from", "on", "about", "against"
        }
        words = re.findall(r'\b\w+\b', text.lower())
        return set(w for w in words if w not in stopwords and len(w) > 2)

    title_words = clean_and_tokenize(title)
    if not title_words:
        return False

    for exist in existing_titles:
        exist_words = clean_and_tokenize(exist)
        if not exist_words:
            continue

        intersection = len(title_words.intersection(exist_words))
        union = len(title_words.union(exist_words))
        if union > 0:
            jaccard = intersection / union
            if jaccard >= threshold:
                return True
    return False


def summarize_text_concise(title: str, description: str = "", content: str = "") -> str:
    """
    Local extractive summarizer parsing text using local sentence splitting rules.
    Returns the first 3 concise sentences.
    """
    text_source = description if description and len(description.strip()) > 30 else content
    if not text_source or not text_source.strip():
        text_source = title

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', (text_source or "").strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 8]

    if not sentences:
        return title or "No summary available."

    # Return first 3 sentences
    return " ".join(sentences[:3])


def get_news_sentiment(title: str, description: str) -> str:
    """
    Lexicon-based news sentiment scoring.
    Returns 'Positive', 'Negative', or 'Neutral'.
    """
    text = ((title or "") + " " + (description or "")).lower()

    negative_words = {
        "kill", "die", "crash", "dead", "arrest", "scam", "crisis", "fire", "threat",
        "clash", "loss", "inflation", "protest", "strike", "court", "accuse", "warn", "suspect"
    }

    positive_words = {
        "win", "gain", "grow", "success", "launch", "develop", "benefit", "celebrate",
        "support", "peace", "summit", "achieve", "rescue", "save", "profit", "boost"
    }

    words = set(re.findall(r'\b\w+\b', text))
    neg_hits = len(words.intersection(negative_words))
    pos_hits = len(words.intersection(positive_words))

    if neg_hits > pos_hits:
        return "Negative"
    elif pos_hits > neg_hits:
        return "Positive"
    else:
        return "Neutral"
