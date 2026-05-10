# ============================================
# tools/search_tool.py  — with Market Alerts
# ============================================

import re
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

# Crops we monitor for price alerts
_PRICE_CROPS = {
    "wheat", "rice", "maize", "corn", "cotton", "sugarcane",
    "tomato", "onion", "potato", "garlic", "mango", "orange",
    "gandum", "chawal", "tamatar", "pyaz"
}

def _detect_crop(query: str) -> str | None:
    """Return matched crop name if query is price-related."""
    ql = query.lower()
    if not any(w in ql for w in ["price", "rate", "cost", "qeemat", "mandi", "market"]):
        return None
    for crop in _PRICE_CROPS:
        if crop in ql:
            return crop
    return None


def _extract_price_change(text: str) -> float | None:
    """Look for percentage mentions like +25% or dropped 30% in search results."""
    patterns = [
        r"(?:increase[d]?|rise|up|gain[ed]?)\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*%",
        r"(\d+(?:\.\d+)?)\s*%\s*(?:increase|rise|higher|up)",
        r"(?:drop[ped]?|fall|declin[e|ed]?|down|decrease[d]?)\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*%",
        r"(\d+(?:\.\d+)?)\s*%\s*(?:drop|fall|lower|down|decrease)",
    ]
    for i, pat in enumerate(patterns):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            return val if i < 2 else -val   # positive = rise, negative = drop
    return None


@tool
def web_search(query: str) -> str:
    """Search the internet for agricultural information, crop prices, disease info, or news.
    Use for: crop diseases, pesticide data, market prices, weather news, agri news.
    Args:
        query: The search query string in English or Urdu.
    Returns:
        Search results as plain text.
    """
    try:
        ddg    = DuckDuckGoSearchRun(region="pk-en")
        result = ddg.run(query)
        output = result if result else "No results found. Try a different query."

        # ── ALERT HOOK ───────────────────────────────────────
        try:
            crop   = _detect_crop(query)
            change = _extract_price_change(output) if crop else None
            if crop and change is not None and abs(change) >= 20:
                from utils.alert_manager import get_alert_manager
                direction = "risen" if change > 0 else "dropped"
                advice    = (
                    f"Prices have {direction} significantly. "
                    f"{'Consider selling soon if you have stock.' if change > 0 else 'Wait for recovery before selling.'}"
                )
                get_alert_manager().send_price_alert(
                    crop=crop.title(), change_pct=change, advice=advice
                )
        except Exception:
            pass   # Never crash agent on alert failure
        # ─────────────────────────────────────────────────────

        return output
    except Exception as e:
        return f"Search unavailable: {str(e)}"
