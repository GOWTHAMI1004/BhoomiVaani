import re
from collections import Counter


SCRIPT_LANGUAGES = {
    "te": re.compile(r"[\u0c00-\u0c7f]"),
    "hi": re.compile(r"[\u0900-\u097f]"),
    "ta": re.compile(r"[\u0b80-\u0bff]"),
    "kn": re.compile(r"[\u0c80-\u0cff]"),
    "ml": re.compile(r"[\u0d00-\u0d7f]"),
    "bn": re.compile(r"[\u0980-\u09ff]"),
    "gu": re.compile(r"[\u0a80-\u0aff]"),
    "pa": re.compile(r"[\u0a00-\u0a7f]"),
}
SUPPORTED_LANGUAGES = {*SCRIPT_LANGUAGES, "en", "mr"}


def detect_conversation_language(text: str, fallback: str = "en") -> str:
    """Prefer the script of this turn over any language retained from earlier turns."""
    counts = Counter({
        language: len(pattern.findall(text))
        for language, pattern in SCRIPT_LANGUAGES.items()
    })
    detected, count = counts.most_common(1)[0]
    latin_letters = len(re.findall(r"[A-Za-z]", text))
    if count and count >= latin_letters:
        if detected == "hi" and fallback.strip().lower() == "mr":
            return "mr"
        return detected
    if latin_letters:
        return "en"
    normalized_fallback = fallback.strip().lower().split("-", 1)[0]
    return normalized_fallback if normalized_fallback in SUPPORTED_LANGUAGES else "en"
