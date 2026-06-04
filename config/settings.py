# ============================================================
# config/settings.py
# Centralized configuration management
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central settings class — reads from .env file."""

    # Helper to get secret safely
    @staticmethod
    def get_secret(key: str, default: str = "") -> str:
        # Check Streamlit secrets first (for cloud deployment)
        try:
            import streamlit as st
            try:
                if key in st.secrets:
                    return st.secrets[key]
            except Exception:
                pass
        except ImportError:
            pass
        # Fallback to local .env
        import os
        return os.getenv(key, default)

    # --- LLM ---
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # or "gemini", "groq"
    OPENAI_API_KEY: str = get_secret.__func__("OPENAI_API_KEY")
    GROQ_API_KEY: str = get_secret.__func__("GROQ_API_KEY")
    GOOGLE_API_KEY: str = get_secret.__func__("GOOGLE_API_KEY")
    GOOGLE_API_KEYS: list = [k.strip() for k in get_secret.__func__("GOOGLE_API_KEY").split(",") if k.strip()]
    LLM_MODEL_OPENAI: str = "gpt-3.5-turbo"
    LLM_MODEL_GEMINI: str = "gemini-2.5-flash"

    LLM_TEMPERATURE: float = 0.3

    # --- News ---
    NEWS_API_KEY: str = get_secret.__func__("NEWS_API_KEY")

    # --- Alpha Vantage ---
    ALPHA_VANTAGE_KEY: str = get_secret.__func__("ALPHA_VANTAGE_KEY")

    # --- Database ---
    DB_PATH: str = "data/finance_agent.db"

    # --- Cache ---
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # --- Indian Market ---
    MARKET_TIMEZONE: str = "Asia/Kolkata"
    MARKET_OPEN_HOUR: int = 9
    MARKET_OPEN_MINUTE: int = 15
    MARKET_CLOSE_HOUR: int = 15
    MARKET_CLOSE_MINUTE: int = 30

    # Popular Indian stocks with display names
    POPULAR_STOCKS: dict = {
        "RELIANCE.NS": "Reliance Industries",
        "TCS.NS": "Tata Consultancy Services",
        "INFY.NS": "Infosys",
        "HDFCBANK.NS": "HDFC Bank",
        "ICICIBANK.NS": "ICICI Bank",
        "WIPRO.NS": "Wipro",
        "SBIN.NS": "State Bank of India",
        "BAJFINANCE.NS": "Bajaj Finance",
        "BHARTIARTL.NS": "Bharti Airtel",
        "HINDUNILVR.NS": "Hindustan Unilever",
        "LT.NS": "Larsen & Toubro",
        "KOTAKBANK.NS": "Kotak Mahindra Bank",
        "ASIANPAINT.NS": "Asian Paints",
        "TITAN.NS": "Titan Company",
        "ULTRACEMCO.NS": "UltraTech Cement",
        "ADANIENT.NS": "Adani Enterprises",
        "ADANIPORTS.NS": "Adani Ports",
        "AXISBANK.NS": "Axis Bank",
        "BAJAJ-AUTO.NS": "Bajaj Auto",
        "BPCL.NS": "BPCL",
        "CIPLA.NS": "Cipla",
        "COALINDIA.NS": "Coal India",
        "DRREDDY.NS": "Dr. Reddy's",
        "EICHERMOT.NS": "Eicher Motors",
        "GRASIM.NS": "Grasim Industries",
        "HCLTECH.NS": "HCL Tech",
        "HEROMOTOCO.NS": "Hero MotoCorp",
        "HINDALCO.NS": "Hindalco",
        "ITC.NS": "ITC",
        "JSWSTEEL.NS": "JSW Steel",
        "M&M.NS": "Mahindra & Mahindra",
        "MARUTI.NS": "Maruti Suzuki",
        "NESTLEIND.NS": "Nestle India",
        "NTPC.NS": "NTPC",
        "ONGC.NS": "ONGC",
        "POWERGRID.NS": "Power Grid",
        "SUNPHARMA.NS": "Sun Pharma",
        "TATAMOTORS.NS": "Tata Motors",
        "TATASTEEL.NS": "Tata Steel",
        "TECHM.NS": "Tech Mahindra",
        "HAL.NS": "Hindustan Aeronautics Limited",
        "IRFC.NS": "Indian Railway Finance Corporation",
        "RVNL.NS": "Rail Vikas Nigam Limited",
        "ZOMATO.NS": "Zomato Limited",
        "JIOFIN.NS": "Jio Financial Services",
    }

    # Indian market sectors
    SECTORS: dict = {
        "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
        "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
        "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS"],
        "Auto": ["MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS"],
        "Energy": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "IOC.NS"],
    }


settings = Settings()
