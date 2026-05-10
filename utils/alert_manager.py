# ============================================================
# utils/alert_manager.py
# KisanAI Smart Alert System — Gmail SMTP (no paid API)
# Handles: Weather | Disease | Market Price alerts
# ============================================================

import os
import smtplib
import threading
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("KisanAI.Alerts")


# ── HTML email base template ─────────────────────────────────
def _base_template(title: str, body_html: str, alert_color: str = "#2ea043") -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
  .wrap {{ max-width: 620px; margin: 30px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,.12); }}
  .header {{ background: linear-gradient(135deg, #0d2818, #1a472a); padding: 28px 32px; }}
  .logo {{ color: {alert_color}; font-size: 26px; font-weight: 700; letter-spacing: 1px; }}
  .logo span {{ color: #fff; }}
  .tagline {{ color: #8bc34a; font-size: 12px; margin-top: 4px; }}
  .alert-bar {{ background: {alert_color}; padding: 12px 32px; color: #fff; font-weight: 700; font-size: 15px; }}
  .content {{ padding: 28px 32px; color: #333; line-height: 1.7; }}
  .content h2 {{ color: #1a472a; margin-top: 0; }}
  .urdu {{ direction: rtl; text-align: right; font-size: 15px; color: #444; background: #f9fff9; border-right: 4px solid {alert_color}; padding: 12px 16px; border-radius: 0 6px 6px 0; margin: 16px 0; }}
  .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 700; }}
  .badge-low    {{ background: #d4edda; color: #155724; }}
  .badge-medium {{ background: #fff3cd; color: #856404; }}
  .badge-high   {{ background: #f8d7da; color: #721c24; }}
  .box {{ background: #f0fff4; border: 1px solid #c3e6cb; border-radius: 8px; padding: 16px 20px; margin: 16px 0; }}
  .footer {{ background: #f8f9fa; padding: 16px 32px; font-size: 12px; color: #888; text-align: center; border-top: 1px solid #eee; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
  td, th {{ padding: 8px 12px; border-bottom: 1px solid #eee; text-align: left; }}
  th {{ background: #f0fff4; color: #1a472a; font-weight: 700; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="logo">Kisan<span>AI</span></div>
    <div class="tagline">Intelligent Agricultural Advisory System | Pakistan</div>
  </div>
  <div class="alert-bar">{title}</div>
  <div class="content">{body_html}</div>
  <div class="footer">KisanAI &mdash; IMScience Hackathon 2026 &nbsp;|&nbsp; Automated Alert &nbsp;|&nbsp; Do not reply to this email.</div>
</div>
</body>
</html>"""


class AlertManager:
    """Thread-safe email alert manager using Gmail SMTP."""

    def __init__(self, receiver_email: str = None):
        self.sender   = os.getenv("ALERT_EMAIL_SENDER", "")
        self.password = os.getenv("ALERT_EMAIL_PASSWORD", "")
        self.receiver = receiver_email or os.getenv("ALERT_EMAIL_RECEIVER", self.sender)
        self._enabled = bool(self.sender and self.password)

    def _send_email(self, subject: str, html_body: str) -> bool:
        """Send HTML email via Gmail SMTP. Returns True on success."""
        if not self._enabled or not self.receiver:
            logger.warning("Alert email not configured — skipping.")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[KisanAI] {subject}"
            msg["From"]    = f"KisanAI Alerts <{self.sender}>"
            msg["To"]      = self.receiver
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.receiver, msg.as_string())
            logger.info("Alert email sent to %s", self.receiver)
            return True
        except Exception as exc:
            logger.warning("Alert email failed: %s", exc)
            return False

    def _send_async(self, subject: str, html_body: str):
        """Fire-and-forget: send in background thread so agents never block."""
        t = threading.Thread(target=self._send_email, args=(subject, html_body), daemon=True)
        t.start()

    # ── ALERT 1: Weather ──────────────────────────────────────
    def send_weather_alert(self, city: str, temp: float,
                           wind_kmh: float, condition: str,
                           farming_advice: str):
        """Send weather alert email if thresholds are breached."""
        alerts = []
        color  = "#2ea043"

        if temp < 5:
            alerts.append(("Frost Warning / پالے کی وارننگ", "#1565c0"))
            color = "#1565c0"
        if temp > 42:
            alerts.append(("Heatwave Warning / گرمی کی لہر", "#c62828"))
            color = "#c62828"
        if wind_kmh > 40:
            alerts.append(("Storm Warning / طوفان کی وارننگ", "#6a1b9a"))
            color = "#6a1b9a"
        if "rain" in condition.lower():
            alerts.append(("Heavy Rain Warning / شدید بارش کی وارننگ", "#0277bd"))
            color = "#0277bd"

        if not alerts:
            return  # No threshold breached

        alert_labels = " | ".join(a[0] for a in alerts)
        rows = "".join(
            f"<tr><td>{k}</td><td><b>{v}</b></td></tr>"
            for k, v in [
                ("City / شہر", city),
                ("Temperature", f"{temp}°C"),
                ("Wind Speed", f"{wind_kmh} km/h"),
                ("Condition", condition),
            ]
        )
        body = f"""
        <h2>Weather Alert for {city}</h2>
        <table><tr><th>Parameter</th><th>Value</th></tr>{rows}</table>
        <div class="box"><b>Farming Advice (English):</b><br>{farming_advice}</div>
        <div class="urdu">
            <b>کسانوں کے لیے مشورہ:</b><br>
            موسم کی تبدیلی کی وجہ سے فوری اقدامات کریں۔ اگر ٹھنڈ ہو تو فصل کو ڈھانپیں۔
            اگر طوفان یا بارش ہو تو سپرے ملتوی کریں۔ پانی کا انتظام کریں۔
        </div>"""
        self._send_async(f"Weather Alert: {alert_labels} — {city}",
                         _base_template(f"ALERT: {alert_labels}", body, color))

    # ── ALERT 2: Crop Disease ─────────────────────────────────
    def send_disease_alert(self, disease: str, severity: str,
                           treatment: str, pesticide: str = ""):
        """Send disease diagnosis email after GPT-4o vision analysis."""
        sev_upper = severity.upper()
        badge_cls = {"LOW": "badge-low", "MEDIUM": "badge-medium", "HIGH": "badge-high"}.get(
            sev_upper, "badge-medium")
        color = {"LOW": "#2ea043", "MEDIUM": "#e3b341", "HIGH": "#f85149"}.get(
            sev_upper, "#e3b341")
        warning_html = ""
        if sev_upper == "HIGH":
            warning_html = (
                "<div style='background:#f8d7da;border:1px solid #f5c6cb;"
                "padding:14px;border-radius:8px;color:#721c24;margin:12px 0;'>"
                "<b>HIGH SEVERITY — Immediate action required / فوری توجہ ضروری ہے</b></div>"
            )
        pesticide_row = (f"<tr><td>Suggested Pesticide</td><td><b>{pesticide}</b></td></tr>"
                         if pesticide else "")
        rows = (f"<tr><td>Disease / Problem</td><td><b>{disease}</b></td></tr>"
                f"<tr><td>Severity</td><td><span class='badge {badge_cls}'>{severity}</span></td></tr>"
                f"{pesticide_row}")
        body = f"""
        <h2>Crop Disease Diagnosis Report</h2>
        {warning_html}
        <table><tr><th>Item</th><th>Detail</th></tr>{rows}</table>
        <div class="box"><b>Recommended Treatment:</b><br>{treatment}</div>
        <div class="urdu">
            <b>فصل کی بیماری کی رپورٹ:</b><br>
            آپ کی فصل میں <b>{disease}</b> کی بیماری کی نشاندہی ہوئی ہے۔
            شدت: <b>{severity}</b>۔ فوری علاج کریں اور ماہر زرعی کارکن سے مشورہ لیں۔
        </div>"""
        self._send_async(f"Crop Disease Alert: {disease} ({severity} Severity)",
                         _base_template("CROP DISEASE DIAGNOSIS REPORT", body, color))

    # ── ALERT 3: Market Price ─────────────────────────────────
    def send_price_alert(self, crop: str, change_pct: float, advice: str):
        """Send market price alert when significant price movement detected."""
        direction = "INCREASE" if change_pct > 0 else "DROP"
        color     = "#2ea043" if change_pct > 0 else "#f85149"
        urdu_dir  = "اضافہ" if change_pct > 0 else "کمی"
        rows = (f"<tr><td>Crop / فصل</td><td><b>{crop}</b></td></tr>"
                f"<tr><td>Price Change</td><td><b style='color:{color}'>"
                f"{change_pct:+.1f}% ({direction})</b></td></tr>")
        body = f"""
        <h2>Market Price Alert — {crop}</h2>
        <table><tr><th>Item</th><th>Detail</th></tr>{rows}</table>
        <div class="box"><b>Market Advice:</b><br>{advice}</div>
        <div class="urdu">
            <b>مارکیٹ الرٹ:</b><br>
            <b>{crop}</b> کی قیمت میں <b>{abs(change_pct):.0f}%</b> کا {urdu_dir} ہوا ہے۔
            ابھی خریدنے یا بیچنے کا فیصلہ سوچ سمجھ کر کریں۔
        </div>"""
        self._send_async(f"Market Price Alert: {crop} {change_pct:+.0f}%",
                         _base_template(f"MARKET ALERT: {crop} Price {direction}", body, color))


# ── Module-level singleton (loaded once, shared across tools) ─
_default_manager: AlertManager | None = None

def get_alert_manager(receiver: str = None) -> AlertManager:
    """Get or create AlertManager. Pass receiver to override .env default."""
    global _default_manager
    if receiver:
        return AlertManager(receiver_email=receiver)
    if _default_manager is None:
        _default_manager = AlertManager()
    return _default_manager
