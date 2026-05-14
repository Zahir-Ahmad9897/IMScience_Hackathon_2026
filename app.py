# ============================================================
# app.py — KisanAI  |  Production Multi-Agent Chat
# Farmer · Customer · Crop Doctor
# Bilingual EN/UR · Voice I/O · GPT-4o Image Analysis
# Context-Aware Memory via LangGraph SQLite Checkpointer
# LangSmith Real-Time Tracing
# ============================================================

import os, sys, uuid

import streamlit as st
from dotenv import load_dotenv

_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_DIR, ".env"))

os.environ["LANGCHAIN_PROJECT"]    = "KisanAI-MultiAgent"
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="KisanAI — Smart Farm Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═════════════════════════════════════════════════════════════
# PREMIUM DARK CSS
# ═════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Nastaliq+Urdu:wght@400;700&display=swap');

:root {
  --bg:      #0d1117;
  --card:    #161b22;
  --hover:   #1c2128;
  --border:  #30363d;
  --green:   #3fb950;
  --glow:    rgba(63,185,80,0.15);
  --teal:    #39d0c4;
  --gold:    #e3b341;
  --blue:    #58a6ff;
  --muted:   #8b949e;
  --text:    #e6edf3;
  --r:       12px;
}
html, body, [class*="css"] {
  font-family:'Inter',sans-serif;
  background:var(--bg)!important;
  color:var(--text)!important;
}
#MainMenu,footer,header{visibility:hidden}
.stDeployButton{display:none}
.block-container{padding:1.5rem 2rem;max-width:1280px}

/* ── Header ── */
.header-card{background:linear-gradient(135deg,#0d2818,#0d1117 50%,#0a1a2e);
    border:1px solid var(--border);border-radius:var(--r);
    padding:1.5rem 2rem;margin-bottom:1.2rem;position:relative;overflow:hidden}
.header-card::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;
    background:radial-gradient(ellipse at 20% 50%,rgba(63,185,80,.08),transparent 60%);
    animation:gp 4s ease-in-out infinite}
@keyframes gp{0%,100%{opacity:.6}50%{opacity:1}}
.header-title{font-size:2rem;font-weight:700;
    background:linear-gradient(90deg,#3fb950,#39d0c4,#58a6ff);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0}
.header-subtitle{color:var(--muted);font-size:.9rem;margin-top:.3rem}
.role-badge{display:inline-flex;align-items:center;gap:.4rem;padding:.3rem .9rem;
    border-radius:20px;font-size:.82rem;font-weight:600;margin-top:.7rem}
.role-badge-farmer{background:#1a3a1a;border:1px solid #3fb950;color:#3fb950}
.role-badge-customer{background:#2a2a0a;border:1px solid #e3b341;color:#e3b341}
.role-badge-doctor{background:#1a1a3a;border:1px solid #58a6ff;color:#58a6ff}

/* ── Sidebar ── */
section[data-testid="stSidebar"]{background:var(--card)!important;border-right:1px solid var(--border)}
section[data-testid="stSidebar"] .block-container{padding:.8rem}

/* ── Chat — assistant = cream white, user = dark ── */
.stChatMessage{border-radius:var(--r)!important;margin-bottom:.7rem!important;border:none!important}

/* Assistant bubble — warm cream */
.stChatMessage[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]){
    background:#fdfaf5!important;
    border:1px solid #e8e0d0!important;
    border-left:4px solid #2ea043!important;
    box-shadow:0 2px 12px rgba(0,0,0,.08)!important}
.stChatMessage[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) p{
    color:#1a1a1a!important;line-height:1.8}
.stChatMessage[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) *{
    color:#1a1a1a!important}

/* User bubble — dark card */
.stChatMessage[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){
    background:#1c2128!important;
    border:1px solid #30363d!important;
    box-shadow:0 1px 6px rgba(0,0,0,.15)!important}

[data-testid="stChatMessageContent"] p{line-height:1.8}

/* ── Urdu RTL ── */
.umsg{direction:rtl;font-family:'Noto Nastaliq Urdu',serif;
      font-size:1.05rem;line-height:2.1;text-align:right;padding:.3rem 0}

/* ── Buttons ── */
.stButton>button{background:linear-gradient(135deg,#238636,#2ea043);
    color:#fff;border:none;border-radius:8px;font-weight:600;
    transition:all .2s ease;width:100%}
.stButton>button:hover{background:linear-gradient(135deg,#2ea043,#3fb950);
    transform:translateY(-1px);box-shadow:0 4px 16px rgba(63,185,80,.3)}

/* ── Input — ChatGPT style ── */
[data-testid="stChatInput"]{
    background:#ffffff!important;
    border:1.5px solid #d1d5da!important;
    border-radius:24px!important;
    box-shadow:0 4px 24px rgba(0,0,0,.18),0 1px 4px rgba(0,0,0,.08)!important;
    padding:4px 8px!important;
    transition:box-shadow .2s,border-color .2s}
[data-testid="stChatInput"]:focus-within{
    border-color:#3fb950!important;
    box-shadow:0 6px 32px rgba(63,185,80,.2),0 2px 8px rgba(0,0,0,.1)!important}
[data-testid="stChatInput"] textarea{
    background:#ffffff!important;
    border:none!important;
    border-radius:20px!important;
    color:#111111!important;
    font-size:1rem!important;
    line-height:1.6!important;
    padding:12px 16px!important;
    resize:none!important;
    box-shadow:none!important;
    outline:none!important}
[data-testid="stChatInput"] textarea::placeholder{
    color:#9ca3af!important;font-size:.95rem}

/* ── Upload ── */
[data-testid="stFileUploader"]{background:var(--card);
    border:2px dashed var(--border);border-radius:var(--r);transition:.2s}
[data-testid="stFileUploader"]:hover{border-color:var(--green)}

/* ── Misc ── */
hr{border-color:var(--border)!important}
.stSelectbox>div>div{background:var(--card)!important;border-color:var(--border)!important}
.ib{background:#1c2128;border-left:3px solid var(--green);
    border-radius:0 8px 8px 0;padding:.55rem .85rem;margin:.4rem 0;
    font-size:.85rem;color:var(--muted)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--green);
     display:inline-block;margin-right:6px;animation:bk 2s infinite}
@keyframes bk{0%,100%{opacity:1}50%{opacity:.3}}

/* ── Memory badge ── */
.mem{background:#0d2030;border:1px solid #1f4068;border-radius:8px;
     padding:.4rem .75rem;font-size:.78rem;color:#58a6ff;margin:.3rem 0}
</style>
""", unsafe_allow_html=True)

from utils.database import get_recent_threads, get_thread_names
from ui.sidebar import render_sidebar, ROLES
from ui.image_panel import render_image_panel
from ui.voice_panel import render_voice_panel
from ui.chat import render_chat_interface

# ═════════════════════════════════════════════════════════════
# SESSION STATE — initialise once
# ═════════════════════════════════════════════════════════════
def _init():
    defs = {
        "user_role":      "farmer",
        "language":       "auto",
        "msg_history":    [],
        "thread_id":      None,
        "past_threads":   [],
        "thread_names":   {},   # {thread_id: display_name} like ChatGPT
        "img_context":    "",
        "tts_on":         False,
        "tts_lang":       "ur",
        # Alert system
        "alert_email":    os.getenv("ALERT_EMAIL_RECEIVER", ""),
        "alert_weather":  True,
        "alert_disease":  True,
        "alert_market":   True,
    }
    for k, v in defs.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Load past threads from SQLite
    if not st.session_state["past_threads"]:
        st.session_state["past_threads"] = get_recent_threads(50)

    if not st.session_state["thread_names"]:
        st.session_state["thread_names"] = get_thread_names()

    # Create default thread
    if not st.session_state["thread_id"]:
        tid = uuid.uuid4().hex[:12]
        st.session_state["thread_id"] = tid
        if tid not in st.session_state["past_threads"]:
            st.session_state["past_threads"].insert(0, tid)

_init()

# ═════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════
render_sidebar()

# ═════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════
role_icon, role_label, role_css = ROLES[st.session_state["user_role"]]
role_css_map = {
    "rf": "role-badge-farmer",
    "rc": "role-badge-customer",
    "rd": "role-badge-doctor"
}
mem_count = len(st.session_state["msg_history"])

st.markdown(f"""
<div class='header-card'>
  <div class='header-title'>🌾 KisanAI — Smart Farm Assistant</div>
  <div class='header-subtitle'>Multi-Agent · Bilingual (English + اردو) · Context-Aware Memory · LangSmith Traced</div>
  <div class='role-badge {role_css_map.get(role_css, "role-badge-farmer")}'>{role_icon} {role_label} Mode</div>
  <div class='mem' style='display:inline-block;margin-left:1rem'>
    💾 {mem_count // 2} exchanges in memory · Session: {st.session_state['thread_id']}
  </div>
</div>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════
# PANELS & CHAT INTERFACE
# ═════════════════════════════════════════════════════════════
render_image_panel()
render_voice_panel()
render_chat_interface()
