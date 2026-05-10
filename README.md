# KisanAI — Intelligent Multi-Agent Agricultural Advisory System

> **IMScience Hackathon 2026** | GPT-4o + LangGraph + Streamlit | Built for Pakistan Agriculture

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1-green)](https://github.com/langchain-ai/langgraph)
[![GPT-4o](https://img.shields.io/badge/GPT--4o-OpenAI-blueviolet)](https://openai.com)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)](https://streamlit.io)

---

## What is KisanAI?

KisanAI is a production-grade, **bilingual (English + Urdu)** multi-agent advisory system for Pakistan's agricultural sector. Three specialized AI agents collaborate under a LangGraph supervisor to give farmers, customers, and crop doctors expert advice in real-time — with voice, image, and smart email alerts.

---

## Live Demo Features

| Feature | Description |
|---------|-------------|
| 3 AI Agents | Farmer / Customer / Crop Doctor — each GPT-4o powered |
| Bilingual | Auto-detects English or Urdu — Urdu renders RTL |
| Voice Input | Whisper AI transcribes Urdu/English speech |
| Crop Vision | Upload photo — GPT-4o diagnoses disease/pest |
| Smart Alerts | Email alerts for weather, disease, market prices |
| Demo Slider | Slide temperature to trigger live alert email |
| Memory | Full conversation history per session (SQLite) |
| LangSmith | Real-time agent trace in LangSmith dashboard |

---

## System Architecture

```
+----------------------------------------------------------+
|                    STREAMLIT FRONTEND                    |
|  Role Selector | Chat | Voice | Image | Demo Alert Slider|
+---------------------------+------------------------------+
                            |
                            v
+----------------------------------------------------------+
|              LANGGRAPH SUPERVISOR / ROUTER               |
|   user_role --> routes to agent                          |
|   SQLite Checkpointer --> Full conversation memory       |
|   LangSmith --> Real-time trace every agent call         |
+----------+-----------------+----------------+-----------+
           |                 |                |
           v                 v                v
  +----------------+ +---------------+ +----------------+
  |  FARMER AGENT  | |CUSTOMER AGENT | | DOCTOR AGENT   |
  |  GPT-4o        | |  GPT-4o       | |  GPT-4o        |
  |  (Agronomist)  | |  (Market Adv) | |  (Pathologist) |
  +-------+--------+ +-------+-------+ +--------+-------+
          |                  |                   |
          +------------------+-------------------+
                             |
               +-------------+-------------+
               |    SHARED TOOLS            |
               |  web_search  (DuckDuckGo)  |
               |  get_weather (OpenWeather)  |
               |  analyze_crop (GPT-4o Vis) |
               |  agri_calculator           |
               +-------------+-------------+
                             |
               +-------------+-------------+
               |   ALERT SYSTEM             |
               |  WeatherAlert  (email)     |
               |  DiseaseAlert  (email)     |
               |  MarketAlert   (email)     |
               +----------------------------+
```

---

## Agent Flow

```
User (Text / Voice / Image)
         |
   [Language Detection]
         |
   [LangGraph routes to agent]
         |
   [GPT-4o processes with tools]
         |
   [Tool called? Search/Weather/Vision/Calc]
         |
   [SQLite saves full state]
         |
   [Response rendered + optional TTS]
         |
   [LangSmith logs trace]
         |
   [Alert email fired if threshold met]
```

---

## Smart Alert System

| Alert | Trigger | Email |
|-------|---------|-------|
| Weather | Temp >42C / <5C / Wind >40kmh / Rain | Heatwave / Frost / Storm warning |
| Disease | Every GPT-4o Vision diagnosis | Full HTML disease report |
| Market | Price change >20% detected | Buy/sell advice email |

Demo: Use the **temperature slider** in the sidebar to set any temperature and click **"Send Demo Alert Email"** — a professional HTML email arrives instantly.

---

## Project Structure

```
IMScience_Hackthon2026/
+-- app.py                   # Streamlit UI (dark theme, bilingual)
+-- orchestrator.py          # LangGraph graph + routing + memory
+-- requirements.txt
+-- README.md
+-- .gitignore
|
+-- agents/
|   +-- farmer_agent.py
|   +-- customer_agent.py
|   +-- doctor_agent.py
|
+-- tools/
|   +-- search_tool.py       # DuckDuckGo + market alert hook
|   +-- weather_tool.py      # OpenWeatherMap + weather alert hook
|   +-- vision_tool.py       # GPT-4o Vision + disease alert hook
|   +-- calculator_tool.py
|
+-- utils/
    +-- language.py          # Auto EN/UR detection
    +-- voice.py             # Whisper STT + gTTS TTS
    +-- alert_manager.py     # Gmail SMTP alert system
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agents | OpenAI GPT-4o |
| Orchestration | LangGraph 1.1 |
| Vision | GPT-4o Vision |
| Voice STT | OpenAI Whisper |
| Voice TTS | gTTS |
| Web Search | DuckDuckGo (pk-en) |
| Weather | OpenWeatherMap API |
| Memory | SQLite + LangGraph Checkpointer |
| Tracing | LangSmith |
| Alerts | Gmail SMTP (smtplib) |
| UI | Streamlit |

---

## How to Run

```powershell
# 1. Clone
git clone https://github.com/Zahir-Ahmad9897/IMScience_Hackathon_2026.git
cd IMScience_Hackathon_2026

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up .env (copy template and fill in your keys)
copy .env.example .env

# 4. Run
streamlit run app.py --server.port 8501
```

Open: **http://localhost:8501**

---

## Environment Variables (.env)

```
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
OPENWEATHER_API_KEY=your_weather_key
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
ALERT_EMAIL_SENDER=your_gmail@gmail.com
ALERT_EMAIL_PASSWORD=your_gmail_app_password
ALERT_EMAIL_RECEIVER=farmer_email@gmail.com
```

---

## Built By

**Zahir Ahmad** | IMScience Hackathon 2026
Stack: Python 3.11 | LangGraph | OpenAI GPT-4o | Streamlit | SQLite | Gmail SMTP
