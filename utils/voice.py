# ============================================
# utils/voice.py
# Voice I/O — STT (OpenAI Whisper) + TTS (gTTS)
# ============================================

import os
import io
import tempfile
from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────
# SPEECH-TO-TEXT  (OpenAI Whisper)
# ──────────────────────────────────────────
def transcribe_audio(audio_bytes: bytes, language: str = "ur") -> str:
    """
    Transcribe audio bytes using OpenAI Whisper.
    Supports Urdu ('ur') and English ('en') natively.

    Args:
        audio_bytes: Raw WAV/MP3 audio bytes.
        language: ISO 639-1 code — 'ur' for Urdu, 'en' for English.

    Returns:
        Transcribed text string.
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Write bytes to a temp file (Whisper needs a file-like object with .name)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,    # "ur" for Urdu, "en" for English
                response_format="text"
            )
        os.unlink(tmp_path)
        return str(transcript).strip()

    except ImportError:
        return "[OpenAI not installed — pip install openai]"
    except Exception as e:
        return f"[Transcription error: {str(e)}]"


# ──────────────────────────────────────────
# TEXT-TO-SPEECH  (gTTS)
# ──────────────────────────────────────────
def text_to_speech(text: str, language: str = "ur") -> bytes:
    """
    Convert text to speech audio bytes using gTTS.
    Returns MP3 bytes that can be played via st.audio().

    Args:
        text: Text to convert to speech.
        language: 'ur' for Urdu, 'en' for English.

    Returns:
        MP3 audio as bytes, or empty bytes on failure.
    """
    try:
        from gtts import gTTS

        # gTTS lang codes
        lang_map = {"ur": "ur", "en": "en"}
        gtts_lang = lang_map.get(language, "en")

        tts = gTTS(text=text[:3000], lang=gtts_lang, slow=False)
        mp3_buffer = io.BytesIO()
        tts.write_to_fp(mp3_buffer)
        mp3_buffer.seek(0)
        return mp3_buffer.read()

    except ImportError:
        return b""
    except Exception:
        return b""


# ──────────────────────────────────────────
# Helper: Streamlit audio recorder fallback
# Uses st.audio_input (Streamlit ≥ 1.33)
# ──────────────────────────────────────────
def get_streamlit_audio_bytes() -> bytes | None:
    """
    Get audio bytes from Streamlit's built-in audio recorder.
    Returns raw bytes or None if no audio recorded.
    """
    try:
        import streamlit as st
        audio = st.audio_input("🎙️ Record your voice message")
        if audio is not None:
            return audio.read()
        return None
    except Exception:
        return None
