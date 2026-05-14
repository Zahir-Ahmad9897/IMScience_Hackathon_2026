import streamlit as st
import uuid
from utils.database import get_recent_threads

ROLES = {
    "farmer":   ("🌾", "Farmer / کسان",             "rf"),
    "customer": ("🛒", "Customer / خریدار",          "rc"),
    "doctor":   ("👨‍⚕️", "Crop Doctor / فصل ڈاکٹر", "rd"),
}
ROLE_COLOR = {"farmer": "#3fb950", "customer": "#e3b341", "doctor": "#58a6ff"}

def _restore_thread(tid: str):
    """Load full conversation history from LangGraph checkpointer."""
    from orchestrator import kisan_graph
    from langchain_core.messages import HumanMessage
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
    except Exception as e:
        import logging
        logging.warning(f"Could not restore thread: {e}")
        st.warning(f"Could not restore thread: {e}")
    return []

def _new_thread():
    tid = uuid.uuid4().hex[:12]
    st.session_state["thread_id"]   = tid
    st.session_state["msg_history"] = []
    st.session_state["img_context"] = ""
    if tid not in st.session_state["past_threads"]:
        st.session_state["past_threads"].insert(0, tid)
    st.rerun()

def render_sidebar():
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
        except Exception as e:
            import logging
            logging.warning(f"Could not wire alert manager: {e}")

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
                import logging
                logging.error(f"Demo alert error: {ex}")
                st.error(f"Error: {ex}")

        st.divider()
        st.markdown("""
        <div style='font-size:.72rem;color:#8b949e;text-align:center'>
            GPT-4o Agents + LangGraph<br>
            GPT-4o Vision · Whisper STT<br>
            LangSmith Tracing · SQLite Memory<br>
            Smart Email Alerts · Pakistan Agriculture
        </div>""", unsafe_allow_html=True)
