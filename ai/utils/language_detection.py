"""
PakLaw AI — Language Detection Utility

Detects if the query language is English, Urdu, Roman Urdu, or Hindi.
"""

from langdetect import DetectorFactory, detect_langs

# Set seed for deterministic language detection
DetectorFactory.seed = 0


def detect_language(text: str) -> str:
    """
    Detect user query language.
    Returns:
        One of: 'en', 'ur', 'hi', 'ro' (Roman Urdu/Hindi)
    """
    if not text or len(text.strip()) < 3:
        return "en"

    # Quick script detection (Urdu/Hindi Arabic/Devanagari characters check)
    has_arabic_script = any("\u0600" <= char <= "\u06ff" for char in text)
    has_devanagari_script = any("\u0900" <= char <= "\u097f" for char in text)

    if has_arabic_script:
        return "ur"
    if has_devanagari_script:
        return "hi"

    try:
        langs = detect_langs(text)
        top_lang = langs[0]

        if top_lang.lang == "ur":
            return "ur"
        elif top_lang.lang == "hi":
            return "hi"
        elif top_lang.lang in (
            "en",
            "no",
            "tl",
            "af",
        ):  # Common false positives for Roman Urdu
            # Check if it looks like Roman Urdu (lexical heuristics)
            roman_urdu_words = {
                "kia",
                "kya",
                "hai",
                "hain",
                "aur",
                "pe",
                "se",
                "ka",
                "ki",
                "ko",
                "kar",
                "gaya",
                "tha",
                "raha",
                "he",
                "ho",
            }
            words = set(text.lower().split())
            if len(words.intersection(roman_urdu_words)) >= 1:
                return "ro"
            return "en"
    except Exception:
        pass

    return "en"
