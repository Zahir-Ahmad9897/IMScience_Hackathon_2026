# ============================================
# utils/language.py
# Language detection utility (EN / UR)
# ============================================

try:
    from langdetect import detect, LangDetectException
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False

# Urdu Unicode range: 0600–06FF
_URDU_CHARS = set(chr(c) for c in range(0x0600, 0x0700))


def detect_language(text: str) -> str:
    """
    Detect whether text is Urdu ('ur') or English ('en').
    Uses character-set heuristic first (fast), then langdetect as fallback.
    
    Returns:
        'ur'  — if Urdu/Arabic script detected
        'en'  — if English or other Latin script
    """
    if not text or not text.strip():
        return "en"

    # Fast heuristic: count Urdu script characters
    urdu_count = sum(1 for ch in text if ch in _URDU_CHARS)
    if urdu_count / max(len(text), 1) > 0.2:
        return "ur"

    # Fallback: langdetect library
    if _LANGDETECT_AVAILABLE:
        try:
            lang = detect(text)
            return "ur" if lang in ("ur", "ar", "fa") else "en"
        except LangDetectException:
            pass

    return "en"


def language_label(lang_code: str) -> str:
    """Return human-readable label for language code."""
    return {"ur": "اردو (Urdu)", "en": "English"}.get(lang_code, "English")
