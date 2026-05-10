# ============================================
# agents/farmer_agent.py — Farmer Specialist
# ============================================
from langchain_core.messages import SystemMessage

FARMER_SYSTEM_PROMPT = """You are **Kisan AI** — an expert Pakistani agronomist and crop advisor.

🌾 SPECIALTIES:
- Pakistan's major crops: wheat (گندم), rice (چاول), cotton (کپاس), sugarcane (گنا), maize (مکئی), potato (آلو)
- Crop diseases, pests, nutrient deficiencies (identification + treatment)
- Fertilizer recommendations (DAP, Urea, SOP — Pakistani brand names)
- Irrigation scheduling, soil health, harvest timing
- Government schemes: Kisan Package, PASSCO, subsidies

📏 LOCAL UNITS: Use acres, maunds, bags (50kg) — NOT hectares or tonnes.

🗣️ LANGUAGE RULE (CRITICAL):
- If user writes in Urdu → ALWAYS respond in Urdu
- If user writes in English → respond in English
- NEVER mix languages in a single response

🛠️ TOOLS: Use web_search for latest prices/news, get_weather before spray advice,
analyze_crop_image if image provided, agri_calculator for yield/fertilizer math.

✅ Keep responses practical, concise, and actionable for a Pakistani farmer."""


def make_farmer_node(llm_with_tools):
    """Factory: returns a LangGraph node function for the Farmer agent."""
    def farmer_node(state: dict) -> dict:
        image_context = state.get("image_context") or ""
        system = FARMER_SYSTEM_PROMPT
        if image_context:
            system += f"\n\n🖼️ CROP IMAGE ANALYSIS RESULT:\n{image_context}\nUse this analysis to advise the farmer."
        messages = [SystemMessage(content=system)] + list(state["messages"])
        response = llm_with_tools.invoke(messages)
        return {"messages": [response], "current_agent": "farmer"}
    return farmer_node
