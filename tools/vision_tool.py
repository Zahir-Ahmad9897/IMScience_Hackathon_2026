# ============================================
# tools/vision_tool.py  — with Disease Alerts
# ============================================

import os
import base64
import re
from langchain_core.tools import tool
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def _extract_severity(text: str) -> str:
    """Parse severity from GPT-4o response text."""
    t = text.lower()
    if any(w in t for w in ["severe", "serious", "critical", "high", "شدید"]):
        return "High"
    if any(w in t for w in ["moderate", "medium", "medium", "درمیانہ"]):
        return "Medium"
    return "Low"


def _extract_disease(text: str) -> str:
    """Extract disease name — first bold phrase or first sentence."""
    bold = re.findall(r"\*\*(.+?)\*\*", text)
    if bold:
        return bold[0][:80]
    return text.split(".")[0][:80]


@tool
def analyze_crop_image(
    image_base64: str,
    question: str = "What disease or problem do you see in this crop? Give detailed advice."
) -> str:
    """
    Analyze a crop or plant image using GPT-4o Vision.
    Identifies diseases, pests, nutrient deficiencies, or growth issues.

    Args:
        image_base64: Base64-encoded image string (JPEG or PNG).
        question: Specific question about the crop image.

    Returns:
        Detailed expert analysis of the crop condition.
    """
    if not image_base64:
        return "No image provided. Please upload a crop photo for analysis."

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert agronomist and plant pathologist specializing in "
                        "Pakistan's major crops: wheat, rice, cotton, sugarcane, maize, potato, "
                        "and vegetables. Analyze crop images and provide:\n"
                        "1. Disease/pest/deficiency identification\n"
                        "2. Severity assessment (mild/moderate/severe)\n"
                        "3. Immediate treatment recommendations\n"
                        "4. Preventive measures\n"
                        "5. Estimated yield impact\n"
                        "Be concise, practical, and farmer-friendly. "
                        "If the user asked in Urdu, respond in Urdu."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "high"
                        }}
                    ]
                }
            ],
            max_tokens=800,
            temperature=0.2
        )
        result = response.choices[0].message.content

        # ── ALERT HOOK ───────────────────────────────────────
        try:
            from utils.alert_manager import get_alert_manager
            disease  = _extract_disease(result)
            severity = _extract_severity(result)
            alert    = get_alert_manager()
            alert.send_disease_alert(
                disease=disease,
                severity=severity,
                treatment=result[:600],
                pesticide=""
            )
        except Exception:
            pass   # Never crash agent on alert failure
        # ─────────────────────────────────────────────────────

        return result

    except Exception as e:
        return f"Image analysis failed: {str(e)}. Please ensure the image is valid and try again."
