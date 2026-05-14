import streamlit as st
from utils.voice import transcribe_audio

def render_voice_panel():
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
            except Exception as e:
                audio_input = None
                import logging
                logging.warning(f"Could not load audio input: {e}")
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
