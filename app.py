# ============================================================
# app.py — KisanAI  |  Production Multi-Agent Chat
# Farmer · Customer · Crop Doctor
# Bilingual EN/UR · Voice I/O · GPT-4o Image Analysis
# Context-Aware Memory via LangGraph SQLite Checkpointer
# LangSmith Real-Time Tracing
# ============================================================

import os, sys, base64, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from dotenv import load_dotenv

_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_DIR, ".env"))

os.environ["LANGCHAIN_PROJECT"]    = "KisanAI-MultiAgent"
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")

from langchain_core.messages import HumanMessage, AIMessage
from orchestrator import kisan_graph, connection
from utils.language import detect_language
from utils.voice    import transcribe_audio, text_to_speech

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
.kh{background:linear-gradient(135deg,#0d2818,#0d1117 50%,#0a1a2e);
    border:1px solid var(--border);border-radius:var(--r);
    padding:1.5rem 2rem;margin-bottom:1.2rem;position:relative;overflow:hidden}
.kh::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;
    background:radial-gradient(ellipse at 20% 50%,rgba(63,185,80,.08),transparent 60%);
    animation:gp 4s ease-in-out infinite}
@keyframes gp{0%,100%{opacity:.6}50%{opacity:1}}
.kt{font-size:2rem;font-weight:700;
    background:linear-gradient(90deg,#3fb950,#39d0c4,#58a6ff);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0}
.ks{color:var(--muted);font-size:.9rem;margin-top:.3rem}
.rb{display:inline-flex;align-items:center;gap:.4rem;padding:.3rem .9rem;
    border-radius:20px;font-size:.82rem;font-weight:600;margin-top:.7rem}
.rf{background:#1a3a1a;border:1px solid #3fb950;color:#3fb950}
.rc{background:#2a2a0a;border:1px solid #e3b341;color:#e3b341}
.rd{background:#1a1a3a;border:1px solid #58a6ff;color:#58a6ff}

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

# ═════════════════════════════════════════════════════════════
# CONSTANTS
# ═════════════════════════════════════════════════════════════
ROLES = {
    "farmer":   ("🌾", "Farmer / کسان",             "rf"),
    "customer": ("🛒", "Customer / خریدار",          "rc"),
    "doctor":   ("👨‍⚕️", "Crop Doctor / فصل ڈاکٹر", "rd"),
}
ROLE_COLOR = {"farmer": "#3fb950", "customer": "#e3b341", "doctor": "#58a6ff"}

PLACEHOLDER = {
    "farmer":   "Ask about crops, diseases, fertilizer... / فصلوں کے بارے میں پوچھیں...",
    "customer": "Ask about market prices, selling... / مارکیٹ قیمتوں کے بارے میں پوچھیں...",
    "doctor":   "Ask about crop disease, pesticides... / کیڑے مار دوا کے بارے میں پوچھیں...",
}


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
        try:
            cur = connection.cursor()
            cur.execute(
                "SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id DESC LIMIT 50"
            )
            st.session_state["past_threads"] = [r[0] for r in cur.fetchall()]
        except Exception:
            pass

    # Create default thread
    if not st.session_state["thread_id"]:
        tid = str(uuid.uuid4())[:8]
        st.session_state["thread_id"] = tid
        if tid not in st.session_state["past_threads"]:
            st.session_state["past_threads"].insert(0, tid)

_init()


# ═════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════
def _restore_thread(tid: str):
    """Load full conversation history from LangGraph checkpointer."""
    try:
        cfg = {"configurable": {"thread_id": tid}}
        gs  = kisan_graph.get_state(cfg)
        if gs.values and "messages" in gs.values:
            history = []
            for m in gs.values["messages"]:
                role    = "user" if isinstance(m, HumanMessage) else "assistant"
                content = m.content if isinstance(m.content, str) else (
                    " ".join(p.get("text","") if isinstance(p,dict) else str(p)
                             for p in m.content)
                )
                history.append({"role": role, "content": content})
            return history
    except Exception:
        pass
    return []


def _render_msg(content: str):
    """Render message with RTL support for Urdu."""
    if detect_language(content) == "ur":
        st.markdown(f'<div class="umsg">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(content)


def _new_thread():
    tid = str(uuid.uuid4())[:8]
    st.session_state["thread_id"]   = tid
    st.session_state["msg_history"] = []
    st.session_state["img_context"] = ""
    if tid not in st.session_state["past_threads"]:
        st.session_state["past_threads"].insert(0, tid)
    st.rerun()


# ═════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:.5rem 0 .8rem'>
        <span style='font-size:2.2rem'>🌾</span>
        <div style='font-size:1.1rem;font-weight:700;color:#3fb950'>KisanAI</div>
        <div style='font-size:.72rem;color:#8b949e'>Multi-Agent Farm Assistant</div>
    </div>""", unsafe_allow_html=True)

    # ── Role ──
    st.markdown("**🎭 Role / کردار**")
    for rk, (icon, label, _) in ROLES.items():
        is_active = st.session_state["user_role"] == rk
        prefix    = "✅" if is_active else "   "
        if st.button(f"{prefix} {icon} {label}", key=f"role_{rk}"):
            st.session_state["user_role"]   = rk
            st.session_state["msg_history"] = []
            st.rerun()

    color = ROLE_COLOR[st.session_state["user_role"]]
    lbl   = ROLES[st.session_state["user_role"]][1]
    st.markdown(
        f"<div class='ib'><span class='dot'></span>Active: "
        f"<b style='color:{color}'>{lbl}</b></div>",
        unsafe_allow_html=True
    )

    st.divider()

    # ── Language ──
    st.markdown("**🗣️ Language / زبان**")
    lang_sel = st.radio("lang", ["Auto-detect", "English", "اردو"],
                         label_visibility="collapsed")
    st.session_state["language"] = {
        "Auto-detect": "auto", "English": "en", "اردو": "ur"
    }[lang_sel]

    st.divider()

    # ── TTS ──
    st.markdown("**🔊 Voice Reply**")
    st.session_state["tts_on"] = st.toggle("Enable TTS", value=st.session_state["tts_on"])
    if st.session_state["tts_on"]:
        st.session_state["tts_lang"] = st.selectbox(
            "TTS lang", ["ur","en"],
            format_func=lambda x: "اردو" if x=="ur" else "English"
        )

    st.divider()

    # ── Sessions ──
    st.markdown("**💬 Chat Sessions**")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ New"):
            _new_thread()
    with c2:
        if st.button("🧹 Clear"):
            st.session_state["msg_history"] = []
            st.rerun()

    # Current thread badge
    cur_name = st.session_state["thread_names"].get(
        st.session_state["thread_id"], "New Chat"
    )
    st.markdown(
        f"<div class='mem'>Active: <b>{cur_name}</b></div>",
        unsafe_allow_html=True
    )

    # ── Past sessions — ChatGPT style named list ──
    ROLE_ICON_MAP = {"farmer": "🌾", "customer": "🛒", "doctor": "👨‍⚕️"}
    st.markdown(
        "<div style='font-size:.78rem;color:#8b949e;margin:4px 0 2px'>Recent Chats</div>",
        unsafe_allow_html=True
    )
    for tid in st.session_state["past_threads"][:15]:
        is_cur    = tid == st.session_state["thread_id"]
        chat_name = st.session_state["thread_names"].get(tid, f"Chat {tid}")
        # Truncate to 22 chars
        display   = chat_name[:22] + "..." if len(chat_name) > 22 else chat_name
        bg  = "background:rgba(63,185,80,.12);border-color:#3fb950" if is_cur else "background:#1c2128;border-color:#30363d"
        dot = "<span style='width:7px;height:7px;border-radius:50%;background:#3fb950;display:inline-block;margin-right:6px'></span>" if is_cur else ""
        st.markdown(
            f"<div id='chat_{tid}' style='padding:7px 10px;margin:2px 0;border-radius:8px;"
            f"border:1px solid;cursor:pointer;{bg};transition:.15s'>"
            f"{dot}<span style='color:#e6edf3;font-size:.82rem'>{display}</span></div>",
            unsafe_allow_html=True
        )
        if st.button(display, key=f"tid_{tid}", use_container_width=True,
                     help=chat_name):
            st.session_state["thread_id"]   = tid
            st.session_state["msg_history"] = _restore_thread(tid)
            st.session_state["img_context"] = ""
            st.rerun()

    st.divider()

    # ── Smart Alert Settings ──
    st.markdown("**🔔 Smart Email Alerts**")
    alert_email = st.text_input(
        "Alert Email Address",
        value=st.session_state["alert_email"],
        placeholder="farmer@gmail.com",
        help="Receive weather, disease & market alerts here"
    )
    if alert_email != st.session_state["alert_email"]:
        st.session_state["alert_email"] = alert_email

    a1, a2 = st.columns(2)
    with a1:
        st.session_state["alert_weather"] = st.toggle(
            "Weather", value=st.session_state["alert_weather"], key="tog_w")
        st.session_state["alert_disease"] = st.toggle(
            "Disease", value=st.session_state["alert_disease"], key="tog_d")
    with a2:
        st.session_state["alert_market"]  = st.toggle(
            "Market",  value=st.session_state["alert_market"],  key="tog_m")

    if st.session_state["alert_email"]:
        active = [t for t, on in [
            ("Weather",st.session_state["alert_weather"]),
            ("Disease",st.session_state["alert_disease"]),
            ("Market", st.session_state["alert_market"]),
        ] if on]
        if active:
            st.markdown(
                f"<div class='ib'><span class='dot'></span>"
                f"Alerts ON: <b>{', '.join(active)}</b></div>",
                unsafe_allow_html=True
            )
        else:
            st.caption("All alerts disabled.")
    else:
        st.caption("Enter email above to enable alerts.")

    # Wire receiver into alert_manager for this session
    try:
        from utils.alert_manager import get_alert_manager
        _am = get_alert_manager(receiver=st.session_state["alert_email"] or None)
        _am._enabled = bool(_am.sender and _am.password and st.session_state["alert_email"])
    except Exception:
        pass

    st.divider()

    # ── DEMO MODE — Temperature Alert Trigger ──
    st.markdown("**Demo: Weather Alert**")
    demo_temp = st.slider(
        "Set Temperature (C)",
        min_value=0, max_value=50,
        value=25, step=1,
        help="Slide above 42C to trigger heatwave alert email"
    )

    # Live colour bar
    if demo_temp < 5:
        bar_color, bar_label = "#1565c0", "FROST WARNING"
    elif demo_temp > 42:
        bar_color, bar_label = "#c62828", "HEATWAVE WARNING"
    elif demo_temp > 35:
        bar_color, bar_label = "#e65100", "HOT"
    else:
        bar_color, bar_label = "#2ea043", "NORMAL"

    bar_pct = int(demo_temp / 50 * 100)
    st.markdown(f"""
    <div style='background:#1c2128;border-radius:8px;height:22px;
                margin:4px 0 8px;overflow:hidden;border:1px solid #30363d'>
      <div style='background:{bar_color};width:{bar_pct}%;height:100%;
                  border-radius:8px;transition:width .3s ease;
                  display:flex;align-items:center;padding-left:8px'>
        <span style='color:#fff;font-size:11px;font-weight:700'>
          {demo_temp}C — {bar_label}
        </span>
      </div>
    </div>""", unsafe_allow_html=True)

    if st.button("Send Demo Alert Email", key="demo_send"):
        try:
            from utils.alert_manager import AlertManager
            tip = ("Heatwave — increase irrigation. Avoid spraying."
                   if demo_temp > 42 else
                   "Frost risk — protect crops, delay transplanting."
                   if demo_temp < 5 else
                   "Temperature normal for farming operations.")
            am  = AlertManager(
                receiver_email=st.session_state["alert_email"] or None
            )
            am.send_weather_alert(
                city="Demo City", temp=float(demo_temp),
                wind_kmh=12.0, condition="Clear", farming_advice=tip
            )
            st.success(f"Alert sent to {am.receiver}!")
        except Exception as ex:
            st.error(f"Error: {ex}")

    st.divider()
    st.markdown("""
    <div style='font-size:.72rem;color:#8b949e;text-align:center'>
        GPT-4o Agents + LangGraph<br>
        GPT-4o Vision · Whisper STT<br>
        LangSmith Tracing · SQLite Memory<br>
        Smart Email Alerts · Pakistan Agriculture
    </div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════
role_icon, role_label, role_css = ROLES[st.session_state["user_role"]]
mem_count = len(st.session_state["msg_history"])

st.markdown(f"""
<div class='kh'>
  <div class='kt'>🌾 KisanAI — Smart Farm Assistant</div>
  <div class='ks'>Multi-Agent · Bilingual (English + اردو) · Context-Aware Memory · LangSmith Traced</div>
  <div class='rb {role_css}'>{role_icon} {role_label} Mode</div>
  <div class='mem' style='display:inline-block;margin-left:1rem'>
    💾 {mem_count // 2} exchanges in memory · Session: {st.session_state['thread_id']}
  </div>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
# IMAGE UPLOAD PANEL
# ═════════════════════════════════════════════════════════════
with st.expander("📸 Upload Crop Image for GPT-4o Vision Analysis", expanded=False):
    ci, cp = st.columns([2, 1])
    with ci:
        uploaded = st.file_uploader(
            "Drop your crop photo here",
            type=["jpg","jpeg","png","webp"],
            label_visibility="collapsed"
        )
        img_q = st.text_input(
            "Question about image",
            placeholder="What disease is on my wheat? / میری گندم میں کیا ہے؟"
        )
        analyze_btn = st.button("🔍 Analyze with GPT-4o", disabled=(uploaded is None))

        if analyze_btn and uploaded:
            with st.spinner("🤖 GPT-4o Vision analyzing..."):
                try:
                    from openai import OpenAI
                    client   = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    img_b64  = base64.b64encode(uploaded.read()).decode()
                    question = img_q or "Diagnose this crop and provide precise treatment advice."
                    resp     = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": question},
                                {"type": "image_url", "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}",
                                    "detail": "high"
                                }}
                            ]
                        }],
                        max_tokens=700, temperature=0.15
                    )
                    st.session_state["img_context"] = resp.choices[0].message.content
                    st.success("✅ Analyzed! Send a message to get agent advice based on this image.")
                except Exception as e:
                    st.error(f"Vision error: {e}")

    with cp:
        if uploaded:
            st.image(uploaded, caption="Crop image", use_container_width=True)
        if st.session_state.get("img_context"):
            st.markdown("**📋 Vision Result:**")
            st.markdown(
                f"<div class='ib'>{st.session_state['img_context'][:300]}...</div>",
                unsafe_allow_html=True
            )


# ═════════════════════════════════════════════════════════════
# VOICE INPUT PANEL
# ═════════════════════════════════════════════════════════════
with st.expander("🎙️ Voice Input — Whisper AI (اردو / English)", expanded=False):
    st.markdown("<div class='ib'>Record → Whisper transcribes → agent responds</div>",
                unsafe_allow_html=True)
    vc1, vc2 = st.columns([2,1])
    with vc1:
        vlang_ui = st.radio("Voice lang", ["اردو (ur)", "English (en)"],
                            horizontal=True, label_visibility="collapsed")
        v_lang   = "ur" if "ur" in vlang_ui else "en"
        try:
            audio_input = st.audio_input("Record", label_visibility="collapsed")
        except Exception:
            audio_input = None
            st.info("Upgrade Streamlit: pip install --upgrade streamlit")

    with vc2:
        if audio_input:
            st.audio(audio_input, format="audio/wav")
            if st.button("📤 Transcribe & Send"):
                with st.spinner("🎤 Whisper transcribing..."):
                    raw = audio_input.read() if hasattr(audio_input,"read") else bytes(audio_input)
                    txt = transcribe_audio(raw, language=v_lang)
                    if txt and not txt.startswith("["):
                        st.session_state["_voice"] = txt
                        st.success(f"📝 Transcribed: {txt}")
                        st.rerun()
                    else:
                        st.error(f"Failed: {txt}")


# ═════════════════════════════════════════════════════════════
# CHAT HISTORY
# ═════════════════════════════════════════════════════════════
st.markdown("---")

if not st.session_state["msg_history"]:
    st.markdown(f"""
    <div style='text-align:center;padding:2rem;color:#8b949e'>
        <div style='font-size:2.5rem'>{role_icon}</div>
        <div style='font-size:1rem;margin-top:.5rem'>
            {role_label} agent ready. Start chatting below.
        </div>
        <div style='font-size:.8rem;margin-top:.3rem;color:#484f58'>
            Tip: Switch roles in the sidebar anytime • Upload crop images • Use voice input
        </div>
    </div>""", unsafe_allow_html=True)

for msg in st.session_state["msg_history"]:
    role    = msg["role"]
    content = msg["content"]
    avatar  = role_icon if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar if role == "assistant" else None):
        _render_msg(content)
        if role == "assistant" and st.session_state["tts_on"]:
            aud = text_to_speech(content[:1000], st.session_state["tts_lang"])
            if aud:
                st.audio(aud, format="audio/mp3", autoplay=False)


# ═════════════════════════════════════════════════════════════
# CHAT INPUT
# ═════════════════════════════════════════════════════════════
voice_pre  = st.session_state.pop("_voice", None)
user_input = st.chat_input(PLACEHOLDER.get(st.session_state["user_role"], "Type here..."))
user_input = user_input or voice_pre

if user_input:
    # Detect language
    lang = (detect_language(user_input)
            if st.session_state["language"] == "auto"
            else st.session_state["language"])

    # Auto-name thread on FIRST message (like ChatGPT)
    tid = st.session_state["thread_id"]
    if tid not in st.session_state["thread_names"] or st.session_state["thread_names"][tid] == "New Chat":
        role_prefix = {"farmer": "Farmer", "customer": "Market", "doctor": "Doctor"}[
            st.session_state["user_role"]]
        short = user_input.strip().replace("\n", " ")[:35]
        st.session_state["thread_names"][tid] = f"{role_prefix}: {short}"

    # Show user message immediately
    st.session_state["msg_history"].append({"role":"user","content":user_input})
    with st.chat_message("user", avatar="👤"):
        _render_msg(user_input)

    # ── LangGraph config with LangSmith metadata ──────────────
    config = {
        "configurable": {
            "thread_id": st.session_state["thread_id"],
        },
        # LangSmith grouping — visible in Traces UI
        "run_name": f"KisanAI·{st.session_state['user_role'].title()}·{st.session_state['thread_id']}",
        "tags":     ["kisanai", st.session_state["user_role"], lang],
        "metadata": {
            "user_role":   st.session_state["user_role"],
            "language":    lang,
            "session_id":  st.session_state["thread_id"],
            "has_image":   bool(st.session_state.get("img_context")),
        },
    }

    # ── Graph invocation state ────────────────────────────────
    # Only NEW message sent; LangGraph checkpointer holds full history
    invoke_state = {
        "messages":      [HumanMessage(content=user_input)],
        "user_role":     st.session_state["user_role"],
        "language":      lang,
        "image_context": st.session_state.get("img_context",""),
        "current_agent": st.session_state["user_role"],
    }

    # ── Stream response ───────────────────────────────────────
    with st.chat_message("assistant", avatar=role_icon):
        ph  = st.empty()
        out = ""

        with st.spinner(f"{role_icon} {role_label} thinking..."):
            try:
                for event in kisan_graph.stream(
                    invoke_state, config=config, stream_mode="values"
                ):
                    if "messages" in event:
                        last = event["messages"][-1]
                        if isinstance(last, AIMessage):
                            if last.tool_calls:
                                out = "🔧 *Calling specialist tools...*"
                            else:
                                c = last.content
                                if isinstance(c, list):
                                    c = " ".join(
                                        p.get("text","") if isinstance(p,dict) else str(p)
                                        for p in c
                                    )
                                out = str(c)
                            ph.markdown(out)
            except Exception as e:
                out = f"⚠️ Agent error: {str(e)}"
                ph.markdown(out)

        # Final render with RTL if Urdu
        if out and detect_language(out) == "ur":
            ph.markdown(f'<div class="umsg">{out}</div>', unsafe_allow_html=True)

        # TTS
        if out and st.session_state["tts_on"]:
            aud = text_to_speech(out[:1000], st.session_state["tts_lang"])
            if aud:
                st.audio(aud, format="audio/mp3", autoplay=True)

    # Persist to UI history (LangGraph already saved to SQLite)
    if out and not out.startswith(("🔧","⚠️")):
        st.session_state["msg_history"].append({"role":"assistant","content":out})
        st.session_state["img_context"] = ""   # consumed after first use
