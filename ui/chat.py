import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from orchestrator import kisan_graph
from utils.language import detect_language
from utils.voice import text_to_speech
from utils.database import save_thread_name
from ui.sidebar import ROLES, ROLE_COLOR

PLACEHOLDER = {
    "farmer":   "Ask about crops, diseases, fertilizer... / فصلوں کے بارے میں پوچھیں...",
    "customer": "Ask about market prices, selling... / مارکیٹ قیمتوں کے بارے میں پوچھیں...",
    "doctor":   "Ask about crop disease, pesticides... / کیڑے مار دوا کے بارے میں پوچھیں...",
}

def _render_msg(content: str):
    """Render message with RTL support for Urdu."""
    if detect_language(content) == "ur":
        st.markdown(f'<div class="umsg">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(content)

def render_chat_interface():
    role_icon, role_label, role_css = ROLES[st.session_state["user_role"]]
    
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
            new_name = f"{role_prefix}: {short}"
            st.session_state["thread_names"][tid] = new_name
            save_thread_name(tid, new_name)

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
                    import logging
                    logging.error(f"Agent error: {e}")
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
