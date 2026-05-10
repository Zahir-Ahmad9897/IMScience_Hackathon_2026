# ============================================
# orchestrator.py — KisanAI Multi-Agent Graph
# LLM: OpenAI GPT-4o (best tool-use + multilingual)
# Tracing: LangSmith real-time debugging
# Memory: SQLite per-thread (full context-aware)
# ============================================

import os
import sqlite3
from typing import Annotated, TypedDict

from dotenv import load_dotenv

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_THIS_DIR, ".env"))

# ── LangSmith — real-time tracing ────────────────────────────
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_ENDPOINT"]   = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
os.environ["LANGCHAIN_API_KEY"]    = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"]    = "KisanAI-MultiAgent"

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver

# ── Tools ────────────────────────────────────────────────────
from tools.search_tool     import web_search
from tools.weather_tool    import get_weather
from tools.vision_tool     import analyze_crop_image
from tools.calculator_tool import agri_calculator

# ── Agent factories ──────────────────────────────────────────
from agents.farmer_agent   import make_farmer_node
from agents.customer_agent import make_customer_node
from agents.doctor_agent   import make_doctor_node


# ═══════════════════════════════════════════════════
# STATE SCHEMA
# ═══════════════════════════════════════════════════
class KisanState(TypedDict):
    messages:      Annotated[list[BaseMessage], add_messages]
    user_role:     str   # "farmer" | "customer" | "doctor"
    language:      str   # "en" | "ur"
    image_context: str   # Pre-analyzed GPT-4o image result
    current_agent: str   # Active agent — for post-tool routing


# ═══════════════════════════════════════════════════
# LLM — OpenAI GPT-4o
# Best-in-class tool use, multilingual, + Urdu
# ═══════════════════════════════════════════════════
_llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.15,
    max_tokens=1024,
)

# ── Tool subsets per role ─────────────────────────
_farmer_tools   = [web_search, get_weather, analyze_crop_image, agri_calculator]
_customer_tools = [web_search, agri_calculator]
_doctor_tools   = [analyze_crop_image, web_search, agri_calculator]
_all_tools      = [web_search, get_weather, analyze_crop_image, agri_calculator]

# ── Agent nodes ───────────────────────────────────
farmer_node   = make_farmer_node(_llm.bind_tools(_farmer_tools))
customer_node = make_customer_node(_llm.bind_tools(_customer_tools))
doctor_node   = make_doctor_node(_llm.bind_tools(_doctor_tools))
tool_node     = ToolNode(_all_tools)


# ═══════════════════════════════════════════════════
# ROUTING
# ═══════════════════════════════════════════════════
def route_to_agent(state: KisanState) -> str:
    return state.get("user_role", "farmer")


def route_after_tools(state: KisanState) -> str:
    return state.get("current_agent", "farmer")


# ═══════════════════════════════════════════════════
# GRAPH
# ═══════════════════════════════════════════════════
def build_graph(checkpointer):
    graph = StateGraph(KisanState)

    graph.add_node("farmer_node",   farmer_node)
    graph.add_node("customer_node", customer_node)
    graph.add_node("doctor_node",   doctor_node)
    graph.add_node("tool_node",     tool_node)

    graph.add_conditional_edges(START, route_to_agent, {
        "farmer":   "farmer_node",
        "customer": "customer_node",
        "doctor":   "doctor_node",
    })

    for node_name in ["farmer_node", "customer_node", "doctor_node"]:
        graph.add_conditional_edges(node_name, tools_condition, {
            "tools": "tool_node",
            END:     END,
        })

    graph.add_conditional_edges("tool_node", route_after_tools, {
        "farmer":   "farmer_node",
        "customer": "customer_node",
        "doctor":   "doctor_node",
    })

    return graph.compile(checkpointer=checkpointer)


# ═══════════════════════════════════════════════════
# PERSISTENCE — SQLite
# Cloud Run: filesystem read-only, use /tmp
# Local dev: use project directory
# ═══════════════════════════════════════════════════
_IS_CLOUD = os.getenv("K_SERVICE") is not None  # Cloud Run sets K_SERVICE
_DB_PATH  = "/tmp/database.db" if _IS_CLOUD else os.path.join(_THIS_DIR, "database.db")
connection   = sqlite3.connect(_DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn=connection)

kisan_graph  = build_graph(checkpointer)


# ═══════════════════════════════════════════════════
# TERMINAL SMOKE TEST
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    from langchain_core.messages import HumanMessage

    print("[TEST] Farmer Agent (Urdu) ...")
    config = {"configurable": {"thread_id": "gpt4o-test-farmer"}}
    result = kisan_graph.invoke({
        "messages":      [HumanMessage(content="gandum mein peele dhabbay hain, kya bimari hai?")],
        "user_role":     "farmer",
        "language":      "en",
        "image_context": "",
        "current_agent": "farmer",
    }, config=config)
    print("[OK] FARMER:", result["messages"][-1].content[:300])

    print("\n[TEST] Doctor Agent (English + web_search tool) ...")
    config2 = {"configurable": {"thread_id": "gpt4o-test-doctor"}}
    result2 = kisan_graph.invoke({
        "messages":      [HumanMessage(content="What is trichogramma wasp for cotton pest control?")],
        "user_role":     "doctor",
        "language":      "en",
        "image_context": "",
        "current_agent": "doctor",
    }, config=config2)
    print("[OK] DOCTOR:", result2["messages"][-1].content[:300])
