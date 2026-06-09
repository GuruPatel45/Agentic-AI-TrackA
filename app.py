# ============================================================
# app.py — FinSaarthi v2.0  |  Premium UI — Final
# ============================================================


import streamlit as st
import pandas as pd
import time
import os
import logging
import warnings

# 🔥 Suppress DuckDuckGo and other noisy warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*duckduckgo_search.*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*backend='api'.*")

logger = logging.getLogger(__name__)

# 🔥 Suppress unwanted yfinance + network logs
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)



st.set_page_config(
    page_title="FinSaarthi — AI Stock Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config.settings import settings
from database.db_manager import (
    initialize_database, add_to_watchlist, remove_from_watchlist,
    get_watchlist, add_to_portfolio, get_portfolio, remove_from_portfolio,
)
from tools.stock_tools import (
    get_stock_price, get_historical_data, calculate_sip,
    calculate_tax_implications, get_fundamental_analysis,
    batch_fetch_prices
)
from tools.news_tools import get_news_with_sentiment
from tools.ai_signals import get_trading_signal, get_market_mood, calculate_portfolio_risk, get_top_movers, get_sector_heatmap, get_market_breadth, get_52week_pulse
from agents.financial_agent import FinancialAgent
from agents.market_brief import generate_market_brief, generate_comparison_summary
from ui.charts import (
    create_candlestick_chart, create_comparison_chart,
    create_sentiment_gauge, create_portfolio_pie, create_sip_chart,
    create_macd_chart, create_market_mood_chart, create_risk_meter,
    create_signal_chart, create_pnl_chart,
)
from utils import is_market_open, validate_symbol, format_inr, export_analysis_to_pdf
import streamlit.components.v1 as components

def render_interactive_chart(symbol, height=500, key_prefix="chart"):
    # On mobile the col_chart is already full-width, controls stack naturally
    c_hdr, c_int, c_ind = st.columns([2, 1, 1.5])
    with c_hdr:
        sec_hdr(f"{symbol} — Real-Time Interactive Chart", "blue")
    with c_int:
        st.markdown("<div style='margin-top:0.85rem;'></div>", unsafe_allow_html=True)
        interval_opt = st.selectbox(
            "Interval", 
            ["1m", "5m", "15m", "1h", "1d", "1wk"], 
            index=4, 
            label_visibility="collapsed",
            key=f"chart_interval_{key_prefix}_{symbol}"
        )
    with c_ind:
        st.markdown("<div style='margin-top:0.85rem;'></div>", unsafe_allow_html=True)
        indicators_opt = st.multiselect(
            "Indicators",
            ["SMA 20", "SMA 50", "EMA 20", "Bollinger Bands", "MACD", "RSI"],
            default=[],
            label_visibility="collapsed",
            key=f"chart_ind_{key_prefix}_{symbol}"
        )
    
    period_map = {"1m": "5d", "5m": "1mo", "15m": "1mo", "1h": "1y", "1d": "5y", "1wk": "10y"}
    yf_interval = "60m" if interval_opt == "1h" else interval_opt
    
    with st.spinner("Generating premium chart..."):
        from ui.charts import create_interactive_plotly_chart
        from tools.stock_tools import get_historical_data, calculate_technical_indicators
        
        df_chart = get_historical_data(symbol, period=period_map[interval_opt], interval=yf_interval)
        
        if not df_chart.empty:
            if indicators_opt:
                df_chart = calculate_technical_indicators(df_chart)
            fig = create_interactive_plotly_chart(df_chart, symbol, indicators=indicators_opt)
            # Apply dragmode=pan and uirevision so state persists across rerenders
            fig.update_layout(dragmode="pan", uirevision=f"{symbol}_{interval_opt}")
            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"plotly_{key_prefix}_{symbol}_{interval_opt}",
                config={
                    "displayModeBar": False,
                    "scrollZoom": True,
                    "doubleClick": "reset+autosize",
                    "responsive": True,
                }
            )
        else:
            st.warning("⚠️ No data available for the selected interval.")


initialize_database()
os.makedirs("data", exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  MASTER CSS
# ═══════════════════════════════════════════════════════════
from ui.styles import get_responsive_css
st.markdown(get_responsive_css(), unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────
from ui.state_manager import initialize_session_state
initialize_session_state()

# ── GLOBAL URL PARAMETER HANDLER ──────────────────────────
# This only runs when an explicit action (like Delete) is triggered via URL
if "del_wl" in st.query_params:
    try:
        # Support both list-style and string-style parameters
        target = st.query_params.get_all("del_wl")[0] if hasattr(st.query_params, "get_all") else st.query_params["del_wl"]
        if target:
            from database.db_manager import remove_from_watchlist as _rfw
            res = _rfw(target)
            if res.get("success"):
                st.toast(f"🗑️ Removed {target} from watchlist")
            else:
                st.toast(f"⚠️ Failed to remove {target}: {res.get('message')}")
        
        # Force navigation to Watchlist ONLY for this specific deletion rerun
        st.session_state.nav_page = "Watchlist"
        
        # Clear URL params and rerun to clean the browser address bar
        st.query_params.clear()
        time.sleep(0.1)
        st.rerun()
    except Exception as e:
        st.toast(f"❌ URL Action Error: {str(e)}")

def get_agent():
    # Always re-initialize in development to pick up code changes
    # or use a version-based check if performance is a concern.
    # For now, we force re-init if the session is active to fix stale logic issues.
    if st.session_state.agent is None or os.environ.get("FORCE_AGENT_RELOAD", "true") == "true":
        try:
            st.session_state.agent = FinancialAgent()
            st.session_state.agent_error = None
        except Exception as e:
            st.session_state.agent_error = str(e)
    return st.session_state.agent


# ─── HELPER COMPONENTS ────────────────────────────────────
from ui.components import page_header, sec_hdr, ticker_card, prog_bar, stat_row


# ═══════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="padding:0rem 0.2rem 1rem; display:flex; align-items:center; justify-content:center; gap:12px;">
      <!-- Logo -->
      <div style="font-size:2.2rem; filter:drop-shadow(0 0 10px rgba(14,165,233,0.5));">🧊</div>
      <div style="text-align:left;">
        <div style="font-family:'Inter',sans-serif;font-size:1.4rem;font-weight:700;color:#FFF;line-height:1;">FinSaarthi</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.55rem;color:#8892B0;letter-spacing:0.05em;margin-top:4px;">AI INTELLIGENCE</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    def render_market_status():
        m_info = is_market_open()
        is_op = "OPEN" in m_info.get("status", "").upper()
        s_c = "#10B981" if is_op else "#EF4444"
        s_l = "Market Open" if is_op else "Market Closed"
        
        s_bg = "#D1FAE5" if is_op else "#FFD6D6"
        s_tc = "#059669" if is_op else "#E11D48"
        st.markdown(f"""
        <!-- Market Status Pill -->
        <div style="text-align:center; margin-bottom:1.5rem;">
          <div style="background:{s_bg}; border-radius:50px; padding:0.4rem 1rem; display:inline-flex; align-items:center; gap:8px;">
            <span style="color:{s_tc}; font-weight:600; font-size:0.75rem;">{s_l}</span>
            <span style="color:{s_tc}; font-size:0.75rem;">{'📈' if is_op else '📉'}</span>
            <span style="color:#475569; font-weight:600; font-size:0.7rem;">{m_info.get("current_time_ist","")[:5]} IST</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    if hasattr(st, "fragment"):
        render_market_status = st.fragment(run_every="60s")(render_market_status)

    render_market_status()

    st.markdown("""
    <div style="height:1px;background:linear-gradient(90deg,transparent,#1C2D4F 30%,#1C2D4F 70%,transparent);margin:0 0.1rem 0.6rem;"></div>

    <!-- Nav labels -->
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.52rem;color:#2E3F62;
                text-transform:uppercase;letter-spacing:0.16em;font-weight:600;
                padding:0.3rem 0.5rem 0.2rem;">Navigation</div>
    """, unsafe_allow_html=True)

    nav_options = [
        "Dashboard", "Stock Analysis", "Compare Stocks", 
        "News & Sentiment", "Portfolio Tracker", "Watchlist", 
        "Market Brief", "Calculators", "AI Chat",
    ]
    
    if st.session_state.nav_page not in nav_options:
        st.session_state.nav_page = nav_options[0]

    page = st.radio("nav", options=nav_options, key="nav_page_selector", label_visibility="collapsed")
    # Sync with the actual state variable used by the app
    st.session_state.nav_page = page

    # Auto-close sidebar on mobile after navigation
    import time
    components.html("""
    <script>
        // Force re-render on every rerun: """ + str(time.time()) + """
        let attempts = 0;
        const interval = setInterval(() => {
            const parentDoc = window.parent.document;
            if (window.parent.innerWidth <= 992) {
                const sidebar = parentDoc.querySelector('[data-testid="stSidebar"]');
                if (sidebar && sidebar.getAttribute('aria-expanded') === 'true') {
                    let closeBtn = parentDoc.querySelector('[data-testid="stSidebarCollapseButton"] button');
                    if (!closeBtn) closeBtn = sidebar.querySelector('button');
                    if (closeBtn) {
                        closeBtn.click();
                        clearInterval(interval);
                    }
                }
            }
            attempts++;
            if (attempts > 10) clearInterval(interval);
        }, 500);
    </script>
    """, height=0, width=0)

# ═══════════════════════════════════════════════════════════

#  🏠 DASHBOARD
# ═══════════════════════════════════════════════════════════
if page == "Dashboard":
    page_header("Live Overview", "Market Dashboard", "Real-time pulse of Indian equity markets")

    # ── Load dashboard data sequentially to ensure stability ──
    # Native Streamlit caching handles performance safely without dangerous threading hacks.
    _mood_fallback   = {"mood_label":"Neutral ➡️","mood_color":"#F59E0B","mood_score":50,"bullish_pct":40,"neutral_pct":35,"bearish_pct":25,"gainers":0,"losers":0}
    _movers_fallback = {"gainers":[],"losers":[],"all":[]}

    with st.spinner("Fetching market pulse..."):
        try: nifty = get_stock_price("^NSEI")
        except: nifty = {"error": "Unavailable"}
        
        try: sensex = get_stock_price("^BSESN")
        except: sensex = {"error": "Unavailable"}
        
        try: mood_data = get_market_mood()
        except: mood_data = _mood_fallback
        
        try: movers_data = get_top_movers()
        except: movers_data = _movers_fallback
        
        try: heatmap_data = get_sector_heatmap()
        except: heatmap_data = []
        
        try: pulse_data = get_52week_pulse()
        except: pulse_data = {"near_high":[],"near_low":[]}
        
        try: portfolio = get_portfolio()
        except: portfolio = []
        
        try: wl_items = get_watchlist()
        except: wl_items = []

    # ── Top 4 index / portfolio metrics ──────────────────────
    from ui.components import render_metrics_grid
    dash_metrics = []

    # 1. Nifty 50
    if "error" not in nifty:
        dt = "pos" if nifty["change_pct"] >= 0 else "neg"
        dash_metrics.append({"label": "NIFTY 50", "value": f"{nifty['current_price']:,.2f}", "delta_text": f"{nifty['change_pct']:+.2f}%", "delta_type": dt})
    else:
        dash_metrics.append({"label": "NIFTY 50", "value": "N/A", "delta_text": "—", "delta_type": "neu"})

    # 2. Sensex
    if "error" not in sensex:
        dt = "pos" if sensex["change_pct"] >= 0 else "neg"
        dash_metrics.append({"label": "SENSEX", "value": f"{sensex['current_price']:,.2f}", "delta_text": f"{sensex['change_pct']:+.2f}%", "delta_type": dt})
    else:
        dash_metrics.append({"label": "SENSEX", "value": "N/A", "delta_text": "—", "delta_type": "neu"})

    # 3. Portfolio
    if portfolio:
        try:
            portf_syms = [h["symbol"] for h in portfolio]
            from tools.stock_tools import batch_fetch_prices as _bfp
            portf_prices = _bfp(portf_syms)
            total_val = sum(portf_prices.get(h["symbol"], {}).get("current_price", h["buy_price"]) * h["quantity"] for h in portfolio)
            total_inv = sum(h["buy_price"] * h["quantity"] for h in portfolio)
            pnl = total_val - total_inv
            pnl_pct = (pnl / total_inv * 100) if total_inv > 0 else 0
            dt = "pos" if pnl >= 0 else "neg"
            dash_metrics.append({"label": "PORTFOLIO", "value": f"₹{total_val:,.0f}", "delta_text": f"{pnl_pct:+.1f}% profit", "delta_type": dt})
        except:
            dash_metrics.append({"label": "PORTFOLIO", "value": "—", "delta_text": "Refresh", "delta_type": "neu"})
    else:
        dash_metrics.append({"label": "PORTFOLIO", "value": "—", "delta_text": "0 items", "delta_type": "neu"})

    # 4. Watchlist
    dash_metrics.append({"label": "WATCHLIST", "value": str(len(wl_items)), "delta_text": "Tracked", "delta_type": "neu"})

    render_metrics_grid(dash_metrics)

    st.markdown("---")

    # ── Row 2: Mood + Heatmap + 52-Week ──────────────────────
    col_mood, col_gain, col_lose = st.columns([1.1, 1.8, 1.8])

    with col_mood:
        sec_hdr("Market Mood", "blue")
        mc    = mood_data["mood_color"]
        bull  = mood_data["bullish_pct"]
        neu   = mood_data["neutral_pct"]
        bear  = mood_data["bearish_pct"]
        score = mood_data["mood_score"]

        # Theme-Matched Market Mood Card
        dash_val = (2.82 * score)
        mood_label = mood_data["mood_label"].upper()
        
        html_content = f"""<div style="background:var(--surface); backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px); border:1px solid var(--border); border-radius:var(--r24); padding:1.25rem; position:relative; overflow:hidden; box-shadow:0 8px 32px rgba(0,0,0,0.3); margin-top:0.5rem;"><div style="position:absolute; top:-30px; right:-30px; width:100px; height:100px; background:{mc}; opacity:0.04; filter:blur(40px); border-radius:50%;"></div><div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:center; gap:1.5rem;"><div style="position:relative; width:100px; height:100px; flex-shrink:0;"><svg viewBox="0 0 100 100" style="width:100%; height:100%; transform:rotate(-90deg);"><circle cx="50" cy="50" r="44" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="10" /><circle cx="50" cy="50" r="44" fill="none" stroke="{mc}" stroke-width="10" stroke-dasharray="{dash_val}, 282.6" stroke-linecap="round" style="filter:drop-shadow(0 0 8px {mc}66);" /></svg><div style="position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center;"><span style="font-family:'Outfit',sans-serif; font-size:1.8rem; font-weight:900; color:var(--text); line-height:1;">{score}</span><span style="font-family:'JetBrains Mono',monospace; font-size:0.55rem; color:var(--text3); text-transform:uppercase; letter-spacing:0.1em;">Score</span></div></div><div style="flex:1; min-width:220px; text-align:center;"><div style="margin-bottom:0.8rem;"><div style="font-family:'JetBrains Mono',monospace; font-size:0.6rem; color:var(--text3); text-transform:uppercase; letter-spacing:0.2em; margin-bottom:4px;">Sentiment</div><div style="font-family:'Outfit',sans-serif; font-size:1.5rem; font-weight:900; color:{mc}; text-shadow:0 0 20px {mc}44; letter-spacing:-0.5px;">{mood_label}</div></div><div style="display:flex; gap:0.8rem; padding:0.75rem; background:rgba(255,255,255,0.02); border-radius:16px; border:1px solid var(--border);"><div style="flex:1; text-align:center;"><div style="color:var(--green); font-family:'JetBrains Mono',monospace; font-size:0.95rem; font-weight:800;">{bull}%</div><div style="font-size:0.5rem; color:var(--text3); text-transform:uppercase; letter-spacing:0.05em;">Bullish</div></div><div style="width:1px; background:var(--border);"></div><div style="flex:1; text-align:center;"><div style="color:var(--text2); font-family:'JetBrains Mono',monospace; font-size:0.95rem; font-weight:800;">{neu}%</div><div style="font-size:0.5rem; color:var(--text3); text-transform:uppercase; letter-spacing:0.05em;">Neutral</div></div><div style="width:1px; background:var(--border);"></div><div style="flex:1; text-align:center;"><div style="color:var(--red); font-family:'JetBrains Mono',monospace; font-size:0.95rem; font-weight:800;">{bear}%</div><div style="font-size:0.5rem; color:var(--text3); text-transform:uppercase; letter-spacing:0.05em;">Bearish</div></div></div></div></div></div>"""
        st.markdown(html_content, unsafe_allow_html=True)

    # ── SECTOR HEATMAP ───────────────────────────────────────
    with col_gain:
        sec_hdr("Sector Heatmap", "purple")
        if heatmap_data:
            st.markdown('<div class="fin-card" style="padding:1.2rem; margin-top:0.5rem; height: 100%; background: var(--surface); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: var(--r16); box-shadow: 0 4px 20px rgba(0,0,0,0.2);">', unsafe_allow_html=True)
            for sec in heatmap_data[:5]:
                c = "#10B981" if sec["avg_change"] >= 0 else "#EF4444"
                prog_bar(sec["sector"], f"{sec['avg_change']:+.2f}%", min(abs(sec["avg_change"]) * 20 + 10, 100), color=c)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No sector data.")

    # ── 52-WEEK PULSE ────────────────────────────────────────
    with col_lose:
        sec_hdr("52-Week Pulse", "amber")
        near_high = pulse_data.get("near_high", [])
        near_low = pulse_data.get("near_low", [])
        
        if near_high or near_low:
            with st.container(height=360, border=False):
                for p in near_high:
                    ticker_card(p["symbol"] + " 🎯 High", p["company"], p["price"], p["change_pct"])
                for p in near_low:
                    ticker_card(p["symbol"] + " 📉 Low", p["company"], p["price"], p["change_pct"])
        else:
            st.info("No 52-week pulse data.")

    st.markdown("---")

    # ── Market Chart ──────────────────────────────────────────
    if True:
        render_interactive_chart("^NSEI", height=500, key_prefix="dash")


# ═══════════════════════════════════════════════════════════
#  📊 STOCK ANALYSIS
# ═══════════════════════════════════════════════════════════
elif page == "Stock Analysis":
    # ── CSS injected once ────────────────────────────────────
    st.markdown("""
    <style>
    @keyframes sa-pulse{0%,100%{opacity:1}50%{opacity:0.4}}
    @keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}

    /* ── Page header ── */
    .sa-ph { margin-bottom: 1.6rem; text-align: center; }
    .sa-ph-eyebrow {
      font-family:'JetBrains Mono',monospace; font-size:0.6rem; font-weight:700;
      color:var(--blue2); text-transform:uppercase; letter-spacing:0.2em;
      display:flex; align-items:center; justify-content:center; gap:8px; margin-bottom:0.3rem; opacity:0.9;
    }
    .sa-ph-eyebrow::before{content:'';width:18px;height:1.5px;background:var(--blue2);display:inline-block;}
    .sa-ph-title {
      font-family:'Inter',sans-serif; font-size:clamp(1.5rem,4vw,2.1rem);
      font-weight:800; color:#fff; letter-spacing:-0.8px; line-height:1.1;
      margin-bottom:0.3rem; text-align:center;
    }
    .sa-ph-sub {
      font-size:clamp(0.75rem,2vw,0.84rem); color:var(--text3); letter-spacing:0.01em; text-align:center;
    }

    /* ── Search input — style Streamlit's native component ── */
    [data-testid="stTextInput"] > label { display:none !important; }
    [data-testid="stTextInput"] > div > div {
      background: rgba(10,15,30,0.92) !important;
      border: 1.5px solid rgba(14,165,233,0.25) !important;
      border-radius: 14px !important;
      box-shadow: 0 4px 28px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04) !important;
      transition: border-color 0.25s, box-shadow 0.25s !important;
    }
    [data-testid="stTextInput"] > div > div:focus-within {
      border-color: rgba(99,130,246,0.7) !important;
      box-shadow: 0 4px 28px rgba(0,0,0,0.45), 0 0 0 4px rgba(14,165,233,0.12) !important;
    }
    [data-testid="stTextInput"] input {
      color: #fff !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.88rem !important; font-weight: 500 !important;
      padding: 0.72rem 1rem !important;
      background: transparent !important;
      border: none !important; box-shadow: none !important;
    }
    [data-testid="stTextInput"] input::placeholder {
      color: rgba(113,113,122,0.65) !important; font-size:0.82rem !important;
    }
    /* Hide 'Press Enter to apply' helper text - Robust Fix */
    [data-testid="stTextInput"] p, 
    [data-testid="stTextInput"] small,
    [data-testid="InputInstructions"] { 
      display: none !important; 
      visibility: hidden !important;
      height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
    }

    /* ── Analyze button ── */
    [data-testid="baseButton-primary"] {
      background: linear-gradient(135deg,var(--blue) 0%,#6366F1 100%) !important;
      border: none !important; border-radius: 10px !important;
      font-family: 'Inter', sans-serif !important; font-size: 0.82rem !important;
      font-weight: 700 !important; letter-spacing: 0.02em !important;
      box-shadow: 0 4px 18px rgba(14,165,233,0.38) !important;
      transition: all 0.25s !important; padding: 0 1.2rem !important;
    }
    [data-testid="baseButton-primary"]:hover {
      box-shadow: 0 6px 28px rgba(99,102,241,0.55) !important;
      transform: translateY(-1px) !important;
    }

    /* ── Stock hero card — Terminal Edition ── */
    .sa-hero {
      position:relative;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px; 
      margin-top: 2rem;
      margin-bottom: 1.5rem;
      overflow:hidden;
      box-shadow: 0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
    }
    /* Dot-grid background texture */
    .sa-hero::before {
      content:''; position:absolute; inset:0; pointer-events:none; z-index:0;
      background-image: radial-gradient(rgba(255,255,255,0.025) 1px, transparent 1px);
      background-size: 22px 22px;
    }
    /* Left glowing accent bar */
    .sa-hero-bar {
      position:absolute; left:0; top:0; bottom:0; width:3px; z-index:1;
      background: var(--sa-accent, #10B981);
      box-shadow: 0 0 16px var(--sa-accent, #10B981);
    }
    /* Section: company name + badges */
    .sa-hero-head {
      position:relative; z-index:1;
      display:flex; justify-content:space-between; align-items:center;
      padding: 0.85rem 1.3rem 0.65rem 1.3rem;
      border-bottom: 1px solid rgba(255,255,255,0.05);
      flex-wrap:wrap; gap:0.5rem;
    }
    .sa-company {
      font-family:'Inter',sans-serif; font-size:clamp(0.88rem,2vw,1.08rem);
      font-weight:800; color:#fff; letter-spacing:-0.2px; line-height:1.2;
    }
    .sa-bdgs { display:flex; align-items:center; gap:0.32rem; flex-wrap:wrap; }
    .sa-bdg-live {
      display:inline-flex; align-items:center; gap:4px;
      background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.35);
      color:#10B981; border-radius:4px; padding:2px 8px;
      font-family:'JetBrains Mono',monospace; font-size:0.58rem; font-weight:700;
      letter-spacing:0.05em;
    }
    .sa-bdg-sym {
      background:rgba(14,165,233,0.08); border:1px solid rgba(14,165,233,0.25);
      color:var(--blue2); border-radius:4px; padding:2px 8px;
      font-family:'JetBrains Mono',monospace; font-size:0.58rem; font-weight:600;
      letter-spacing:0.04em;
    }
    /* Section: price */
    .sa-hero-body {
      position:relative; z-index:1;
      padding: 0.75rem 1.3rem 0.55rem;
    }
    .sa-price {
      font-family:'JetBrains Mono',monospace; font-size:clamp(1.35rem,3.5vw,1.85rem);
      font-weight:700; color:#fff; letter-spacing:-0.5px; line-height:1; display:inline;
    }
    .sa-chg-pos { display:inline-block; color:#10B981; font-family:'JetBrains Mono',monospace; font-size:0.75rem; font-weight:700; margin-left:0.75rem; vertical-align:middle; }
    .sa-chg-neg { display:inline-block; color:#EF4444; font-family:'JetBrains Mono',monospace; font-size:0.75rem; font-weight:700; margin-left:0.75rem; vertical-align:middle; }
    /* Section: 52W range */
    .sa-range { position:relative; z-index:1; padding: 0.3rem 1.3rem 0.6rem; }
    .sa-range-hdr {
      display:flex; justify-content:space-between; align-items:center;
      font-family:'JetBrains Mono',monospace; font-size:0.56rem;
      color:var(--text4); margin-bottom:0.35rem; text-transform:uppercase; letter-spacing:0.08em;
    }
    .sa-bar {
      width:100%; height:4px; border-radius:4px;
      background:rgba(255,255,255,0.07); position:relative;
    }
    .sa-bar-fill { height:100%; border-radius:4px; background:linear-gradient(90deg,#EF4444 0%,#F59E0B 50%,#10B981 100%); }
    .sa-bar-dot {
      position:absolute; top:50%; transform:translate(-50%,-50%);
      width:10px; height:10px; border-radius:50%;
      background:#fff; border:2px solid var(--sa-accent,var(--blue));
      box-shadow:0 0 10px var(--sa-accent,var(--blue));
    }
    /* Section: stats — 4-col grid with vertical dividers */
    .sa-stats {
      position:relative; z-index:1;
      display:grid; grid-template-columns:repeat(4,1fr);
      border-top: 1px solid rgba(255,255,255,0.05);
    }
    .sa-st {
      padding: 0.6rem 1.1rem;
      border-right: 1px solid rgba(255,255,255,0.05);
      display:flex; flex-direction:column; gap:3px;
    }
    .sa-st:last-child { border-right:none; }
    .sa-sk {
      font-family:'JetBrains Mono',monospace; font-size:0.53rem;
      color:var(--text4); text-transform:uppercase; letter-spacing:0.1em;
    }
    .sa-sv {
      font-family:'JetBrains Mono',monospace; font-size:0.8rem;
      font-weight:700; color:var(--text);
    }
    @media(max-width:768px){
      .sa-stats { grid-template-columns:repeat(2,1fr); }
      .sa-st:nth-child(2) { border-right:none; }
      .sa-st:nth-child(3), .sa-st:nth-child(4) { border-top:1px solid rgba(255,255,255,0.05); }
      .sa-price { font-size:1.4rem; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Page header
    st.markdown("""<div class="sa-ph">
<div class="sa-ph-eyebrow">Deep Dive Analytics</div>
<div class="sa-ph-title">Stock Analysis</div>
<div class="sa-ph-sub">Technical &nbsp;·&nbsp; Fundamental &nbsp;·&nbsp; AI Signal &nbsp;·&nbsp; PDF Export</div>
</div>""", unsafe_allow_html=True)

    if st.session_state.get("selected_symbol") in ["BTC-USD", "RELIANCE.NS"]:
        st.session_state["selected_symbol"] = ""

    col_sym, col_btn = st.columns([3.2, 1])
    with col_sym:
        symbol_raw = st.text_input("__sym", label_visibility="collapsed",
            value=st.session_state.get("selected_symbol", ""),
            placeholder="🔍  Enter symbol  —  e.g. RELIANCE.NS  ·  TCS.NS  ·  HDFCBANK.NS")
    with col_btn:
        analyze_btn = st.button("Analyze →", type="primary", use_container_width=True)

    is_valid, norm_sym = validate_symbol(symbol_raw)

    if not symbol_raw:
        st.markdown('<br>', unsafe_allow_html=True)
        st.info("💡 Enter an Indian stock symbol above to begin deep-dive analysis.")
    elif not is_valid:
        st.warning(f"⚠️ {norm_sym}")

    elif analyze_btn or st.session_state.get("auto_analyze") == norm_sym:
        st.session_state["auto_analyze"]    = norm_sym
        st.session_state["selected_symbol"] = norm_sym

        try:    price_data = get_stock_price(norm_sym)
        except: price_data = {"error": "Could not fetch price data."}

        if "error" in price_data:
            st.error(f"❌ {price_data['error']}")
        else:
            cname   = price_data.get("company_name", norm_sym)
            price   = price_data["current_price"]
            change  = price_data["change"]
            chg_pct = price_data["change_pct"]
            prev_cl = price_data.get("previous_close", price)
            hi52    = price_data.get("52_week_high", price)
            lo52    = price_data.get("52_week_low",  price)
            pe_r    = price_data.get("pe_ratio", "N/A")
            vol     = price_data.get("volume", None)

            chg_color   = "#10B981" if chg_pct >= 0 else "#EF4444"
            chg_arrow   = "▲" if chg_pct >= 0 else "▼"
            chg_cls     = "pos" if chg_pct >= 0 else "neg"
            accent_c    = chg_color

            # 52-week range position (%)
            try:
                range_span = float(hi52) - float(lo52)
                range_pct  = ((price - float(lo52)) / range_span * 100) if range_span > 0 else 50
                range_pct  = max(0, min(100, range_pct))
                lo52_s     = f"₹{float(lo52):,.1f}"
                hi52_s     = f"₹{float(hi52):,.1f}"
            except:
                range_pct  = 50
                lo52_s     = str(lo52)
                hi52_s     = str(hi52)

            vol_s = f"{vol/1_000_000:.2f}M" if vol and vol >= 1_000_000 else (f"{vol/1_000:.1f}K" if vol else "N/A")

            # ── Stock Hero Card ──────────────────────────────
            st.markdown(f'<div class="sa-hero" style="--sa-accent:{accent_c};"><div class="sa-hero-bar"></div><div class="sa-hero-head"><div class="sa-company">{cname}</div><div class="sa-bdgs"><span class="sa-bdg-live"><span style="width:6px;height:6px;border-radius:50%;background:#10B981;display:inline-block;animation:blink 1.2s infinite;"></span>&nbsp;LIVE</span><span class="sa-bdg-sym">{norm_sym}</span></div></div><div class="sa-hero-body"><div class="sa-price">₹{price:,.2f}</div><div class="sa-chg-{chg_cls}">{chg_arrow}&nbsp;₹{abs(change):.2f}&nbsp;({chg_pct:+.2f}%)</div></div><div class="sa-range"><div class="sa-range-hdr"><span>52W Low &nbsp;{lo52_s}</span><span>52-week range</span><span>52W High &nbsp;{hi52_s}</span></div><div class="sa-bar"><div class="sa-bar-fill" style="width:{range_pct:.1f}%;"></div><div class="sa-bar-dot" style="left:{range_pct:.1f}%;"></div></div></div><div class="sa-stats"><div class="sa-st"><div class="sa-sk">Prev Close</div><div class="sa-sv">₹{prev_cl:,.2f}</div></div><div class="sa-st"><div class="sa-sk">Volume</div><div class="sa-sv">{vol_s}</div></div><div class="sa-st"><div class="sa-sk">P/E Ratio</div><div class="sa-sv">{pe_r}</div></div><div class="sa-st"><div class="sa-sk">Day Change</div><div class="sa-sv" style="color:{chg_color};">{chg_arrow}&nbsp;{abs(chg_pct):.2f}%</div></div></div></div>', unsafe_allow_html=True)

            # ── Inject mobile column-stack CSS ──────────────────
            st.markdown("""
            <style>
            /* On mobile, collapse Streamlit's side-by-side columns into a vertical stack */
            @media (max-width: 768px) {
              [data-testid="stHorizontalBlock"].sa-chart-row > div {
                flex: 0 0 100% !important;
                width: 100% !important;
                min-width: 100% !important;
              }
              /* Make chart iframe/canvas fill parent */
              [data-testid="stPlotlyChart"] > div,
              [data-testid="stPlotlyChart"] iframe {
                width: 100% !important;
              }
            }
            </style>
            """, unsafe_allow_html=True)

            # ── Main layout: Chart (left-wide) | Signal (right-narrow) ──
            col_chart, col_sig = st.columns([3.2, 1])

            with col_sig:
                # AI Signal
                sec_hdr("AI Signal", "purple")
                if True:
                    try:    sig = get_trading_signal(norm_sym)
                    except: sig = {"error": "Unavailable"}

                if "error" not in sig:
                    sc   = sig["signal_color"]
                    conf = sig["confidence"]
                    sig_label = sig["signal"]
                    sig_emoji = sig["signal_emoji"]

                    # Color tokens
                    col_map = {"BUY": ("#10B981","rgba(16,185,129,0.08)","rgba(16,185,129,0.28)"),
                               "SELL":("#EF4444","rgba(239,68,68,0.08)","rgba(239,68,68,0.28)"),
                               "HOLD":("#F59E0B","rgba(245,158,11,0.08)","rgba(245,158,11,0.28)")}
                    txt_c, bg_tint, br_tint = col_map.get(sig_label, col_map["HOLD"])

                    # Build reasons HTML
                    def _dot(r):
                        if any(w in r.lower() for w in ["positive","bullish","above","strong","upward"]): return "#10B981"
                        if any(w in r.lower() for w in ["negative","bearish","below","weak","downward"]): return "#EF4444"
                        return "#6B7280"

                    reasons_html = "".join([
                        f'<div style="display:flex;align-items:flex-start;gap:7px;padding:0.3rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
                        f'<div style="width:5px;height:5px;border-radius:50%;margin-top:5px;flex-shrink:0;background:{_dot(r)};"></div>'
                        f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.55);line-height:1.5;">{r}</div>'
                        f'</div>'
                        for r in sig.get("reasons", [])
                    ])

                    st.markdown(f"""
                    <div style="
                      background:linear-gradient(160deg,rgba(10,14,26,0.98) 0%,rgba(14,20,38,0.96) 100%);
                      border:1px solid rgba(255,255,255,0.07);
                      border-radius:14px; overflow:hidden;
                      box-shadow:0 4px 24px rgba(0,0,0,0.4);
                    ">
                      <!-- Header row -->
                      <div style="display:flex;align-items:center;justify-content:space-between;
                                  padding:0.75rem 1rem 0.6rem;
                                  border-bottom:1px solid rgba(255,255,255,0.05);">
                        <div style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;
                                    color:rgba(255,255,255,0.3);text-transform:uppercase;letter-spacing:0.14em;">
                          AI Signal
                        </div>
                        <div style="
                          font-family:'JetBrains Mono',monospace; font-size:0.72rem; font-weight:800;
                          color:{txt_c}; background:{bg_tint}; border:1px solid {br_tint};
                          border-radius:5px; padding:2px 10px; letter-spacing:0.08em;
                        ">{sig_label}</div>
                      </div>
                      <!-- Confidence bar -->
                      <div style="padding:0.6rem 1rem 0.5rem;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                          <span style="font-family:'JetBrains Mono',monospace;font-size:0.56rem;
                                       color:rgba(255,255,255,0.28);text-transform:uppercase;letter-spacing:0.1em;">
                            Confidence
                          </span>
                          <span style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;
                                       font-weight:700;color:{txt_c};">{conf}%</span>
                        </div>
                        <div style="height:3px;background:rgba(255,255,255,0.06);border-radius:3px;overflow:hidden;">
                          <div style="height:100%;width:{conf}%;background:{txt_c};border-radius:3px;
                                      box-shadow:0 0 8px {txt_c}80;"></div>
                        </div>
                      </div>
                      <!-- Reasons -->
                      <div style="padding:0 1rem 0.7rem;">
                        <div style="font-family:'JetBrains Mono',monospace;font-size:0.54rem;
                                    color:rgba(255,255,255,0.2);text-transform:uppercase;
                                    letter-spacing:0.14em;margin-bottom:0.35rem;">Signal Factors</div>
                        {reasons_html}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ {sig.get('error','Unavailable')}")

            with col_chart:
                if True:
                    render_interactive_chart(norm_sym, height=600, key_prefix="analysis")

            # ── Fundamentals ─────────────────────────────────
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            with st.expander("📋 Fundamental Metrics", expanded=True):
                if True:
                    try:    fd = get_fundamental_analysis(norm_sym)
                    except: fd = {"error": "Unavailable"}
                if "error" not in fd:
                    roe   = fd.get("roe","N/A")
                    roa   = fd.get("roa","N/A")
                    roe_s = f"{roe:.1%}" if isinstance(roe, float) else str(roe)
                    roa_s = f"{roa:.1%}" if isinstance(roa, float) else str(roa)
                    mktcap = fd.get("market_cap_cr","N/A")
                    mc_s   = f"₹{mktcap:,.0f} Cr" if isinstance(mktcap, (int,float)) else str(mktcap)

                    # Helper: color for numeric values
                    def val_color(v, good_above=None, bad_above=None):
                        if not isinstance(v, (int,float)): return "var(--text)"
                        if good_above and v > good_above:  return "#10B981"
                        if bad_above  and v > bad_above:   return "#EF4444"
                        return "var(--text)"

                    pe  = fd.get("pe_ratio","N/A")
                    pb  = fd.get("pb_ratio","N/A")
                    eps = fd.get("eps","N/A")
                    de  = fd.get("debt_to_equity","N/A")
                    dy  = fd.get("dividend_yield","N/A")

                    pe_c  = val_color(pe,  bad_above=35)
                    pb_c  = val_color(pb,  bad_above=5)
                    roe_c = "#10B981" if isinstance(roe, float) and roe > 0.15 else "var(--text)"
                    de_c  = "#EF4444" if isinstance(de,  (int,float)) and de > 1.5 else "#10B981" if isinstance(de,(int,float)) and de < 0.5 else "var(--text)"

                    st.markdown("""
                    <style>
                    .fm-section {
                      background: var(--surface);
                      backdrop-filter: blur(16px);
                      border: 1px solid var(--border);
                      border-radius: 16px;
                      padding: 1.1rem 1.2rem 1rem;
                      position: relative; overflow: hidden;
                      box-shadow: 0 4px 15px rgba(0,0,0,0.15);
                      transition: all 0.3s ease;
                    }
                    .fm-section:hover {
                      border-color: rgba(255,255,255,0.2);
                      transform: translateY(-2px);
                      box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                    }
                    .fm-section::before {
                      content:''; position:absolute; top:0; left:0; right:0; height:2px;
                      border-radius:16px 16px 0 0;
                    }
                    .fm-blue::before  { background: linear-gradient(90deg, var(--blue), #06B6D4); }
                    .fm-green::before { background: linear-gradient(90deg, #10B981, #84CC16); }
                    .fm-amber::before { background: linear-gradient(90deg, #F59E0B, #F97316); }

                    .fm-title {
                      display: flex; align-items: center; gap: 7px;
                      margin-bottom: 0.85rem;
                    }
                    .fm-title-icon {
                      width: 28px; height: 28px; border-radius: 8px;
                      display: flex; align-items: center; justify-content: center;
                      font-size: 0.85rem;
                    }
                    .fm-title-text {
                      font-family: 'Inter', sans-serif !important;
                      font-size: 0.88rem; font-weight: 700; letter-spacing: 0.02em;
                    }

                    .fm-metric {
                      display: flex; align-items: center;
                      justify-content: space-between;
                      padding: 0.5rem 0;
                      border-bottom: 1px solid rgba(255,255,255,0.04);
                    }
                    .fm-metric:last-child { border-bottom: none; padding-bottom: 0; }
                    .fm-metric-label {
                      font-size: 0.76rem; color: var(--text3);
                      display: flex; align-items: center; gap: 6px;
                    }
                    .fm-metric-val {
                      font-family: 'JetBrains Mono', monospace !important;
                      font-size: 0.92rem; font-weight: 700;
                    }
                    </style>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.2rem; margin-bottom: 0.5rem;">

                      <!-- VALUATION -->
                      <div class="fm-section fm-blue">
                        <div class="fm-title">
                          <div class="fm-title-icon" style="background:rgba(14,165,233,0.15);">📊</div>
                          <div class="fm-title-text" style="color:var(--blue2);">Valuation</div>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:var(--blue2);display:inline-block;"></span>
                            P/E Ratio
                          </span>
                          <span class="fm-metric-val" style="color:{pe_c};">{pe}</span>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:var(--blue2);display:inline-block;"></span>
                            P/B Ratio
                          </span>
                          <span class="fm-metric-val" style="color:{pb_c};">{pb}</span>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:var(--blue2);display:inline-block;"></span>
                            EPS
                          </span>
                          <span class="fm-metric-val">₹{eps}</span>
                        </div>
                      </div>

                      <!-- PROFITABILITY -->
                      <div class="fm-section fm-green">
                        <div class="fm-title">
                          <div class="fm-title-icon" style="background:rgba(16,185,129,0.15);">💹</div>
                          <div class="fm-title-text" style="color:#34D399;">Profitability</div>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#34D399;display:inline-block;"></span>
                            ROE
                          </span>
                          <span class="fm-metric-val" style="color:{roe_c};">{roe_s}</span>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#34D399;display:inline-block;"></span>
                            ROA
                          </span>
                          <span class="fm-metric-val">{roa_s}</span>
                        </div>
                        <div class="fm-metric" style="border-bottom:none;padding-bottom:0;">
                          <span class="fm-metric-label" style="font-size:0.68rem;color:var(--text4);font-style:italic;">
                            Return on equity &amp; assets
                          </span>
                        </div>
                      </div>

                      <!-- BALANCE SHEET -->
                      <div class="fm-section fm-amber">
                        <div class="fm-title">
                          <div class="fm-title-icon" style="background:rgba(245,158,11,0.15);">🏦</div>
                          <div class="fm-title-text" style="color:#FBBF24;">Balance Sheet</div>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#FBBF24;display:inline-block;"></span>
                            D/E Ratio
                          </span>
                          <span class="fm-metric-val" style="color:{de_c};">{de}</span>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#FBBF24;display:inline-block;"></span>
                            Div Yield
                          </span>
                          <span class="fm-metric-val">{dy}</span>
                        </div>
                        <div class="fm-metric">
                          <span class="fm-metric-label">
                            <span style="width:3px;height:3px;border-radius:50%;background:#FBBF24;display:inline-block;"></span>
                            Market Cap
                          </span>
                          <span class="fm-metric-val" style="font-size:0.78rem;">{mc_s}</span>
                        </div>
                      </div>

                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ Fundamental data unavailable.")

            # ── AI Deep Analysis ─────────────────────────────
            st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
            with st.expander("🤖 AI Deep Analysis", expanded=False):
                agent = get_agent()
                if agent and not st.session_state.agent_error:
                    if True:
                        try:    result = agent.analyze_stock(norm_sym)
                        except Exception as e:
                            logger.error("AI analysis: %s", e)
                            result = {"error": "AI analysis error."}
                    if "error" not in result:
                        st.markdown(f'<div class="fin-card" style="border-left:3px solid var(--blue);line-height:1.75;font-size:0.88rem;color:var(--text2);">{result["ai_analysis"]}</div>', unsafe_allow_html=True)
                        try:
                            pdf_b = export_analysis_to_pdf(norm_sym, cname, price_data, result.get("fundamental_data",{}), result["ai_analysis"])
                            st.download_button("📥 Download PDF Report", data=pdf_b, file_name=f"{norm_sym}_analysis.pdf", mime="application/pdf")
                        except Exception as e:
                            logger.warning("PDF: %s", e)
                    else:
                        st.error(f"❌ {result['error']}")
                else:
                    st.info("⚙️ Configure LLM API key in .env to enable AI analysis.")

            st.markdown("---")
            if st.button(f"⭐ Add {norm_sym.replace('.NS','')} to Watchlist", type="secondary", use_container_width=True):
                res = add_to_watchlist(norm_sym, cname)
                if res["success"]:
                    st.rerun()
                else:
                    st.warning(res["message"])


# ═══════════════════════════════════════════════════════════
#  🔄 COMPARE STOCKS
# ═══════════════════════════════════════════════════════════
elif page == "Compare Stocks":
    page_header("Side by Side", "Compare Stocks", "Multi-stock technical & AI signal comparison")

    # Sector quick-pick
    sec_hdr("Quick Sector Pick", "blue")
    sc_cols = st.columns(len(settings.SECTORS))
    for i, (name, syms) in enumerate(settings.SECTORS.items()):
        if sc_cols[i].button(name, use_container_width=True):
            st.session_state["compare_symbols"] = ", ".join(syms[:3])
            st.rerun()

    default_cmp   = st.session_state.get("compare_symbols", "TCS.NS, INFY.NS, WIPRO.NS")
    symbols_input = st.text_input("Symbols (comma-separated, max 5)", value=default_cmp)
    compare_btn   = st.button("🔄 Compare Now", type="primary")

    if compare_btn:
        raw_syms   = [s.strip() for s in symbols_input.split(",") if s.strip()]
        valid_syms = []
        for s in raw_syms[:5]:
            ok, norm = validate_symbol(s)
            if ok: valid_syms.append(norm)

        if len(valid_syms) < 2:
            st.error("Please enter at least 2 valid symbols.")
        else:
            if True:
                try:
                    from tools.stock_tools import compare_stocks
                    df = compare_stocks(valid_syms)
                except Exception as e:
                    logger.error("compare_stocks: %s", e)
                    df = pd.DataFrame()

            if not df.empty:
                sec_hdr("Metrics Table", "blue")
                st.dataframe(df, use_container_width=True, hide_index=True)

                sec_hdr("AI Signals", "purple")
                sig_cols    = st.columns(len(valid_syms))
                all_signals = []
                for i, sym in enumerate(valid_syms):
                    with sig_cols[i]:
                        with st.spinner(f"{sym.replace('.NS','')}"):
                            try:    sig = get_trading_signal(sym)
                            except: sig = {"error": "N/A"}
                        all_signals.append(sig)
                        if "error" not in sig:
                            slabel = sig["signal"]
                            sc     = sig["signal_color"]
                            bg_c   = {"BUY":"rgba(16,185,129,0.1)","SELL":"rgba(239,68,68,0.1)","HOLD":"rgba(245,158,11,0.1)"}.get(slabel, "rgba(255,255,255,0.05)")
                            br_c   = {"BUY":"rgba(16,185,129,0.25)","SELL":"rgba(239,68,68,0.25)","HOLD":"rgba(245,158,11,0.25)"}.get(slabel, "rgba(255,255,255,0.1)")

                            st.markdown(f"""
                            <div style="background:{bg_c}; border:1px solid {br_c}; border-radius:10px; padding:0.6rem 0.8rem; text-align:center; box-shadow:0 4px 12px rgba(0,0,0,0.2); margin-bottom: 1rem;">
                              <div style="font-family:'JetBrains Mono',monospace;font-size:0.6rem;color:rgba(255,255,255,0.3);text-transform:uppercase;letter-spacing:0.12em;margin-bottom:4px;">{sym.replace('.NS','')}</div>
                              <div style="font-family:'Inter',sans-serif;font-size:1.05rem;font-weight:800;color:{sc};text-shadow:0 0 10px {sc}40;">{slabel}</div>
                              <div style="font-family:'JetBrains Mono',monospace;font-size:0.55rem;color:rgba(255,255,255,0.2);margin-top:5px;letter-spacing:0.05em;">{sig['confidence']}% CONFIDENCE</div>
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.caption(f"N/A — {sym.replace('.NS','')}")

                st.markdown("<div style='margin-top: 2.5rem;'></div>", unsafe_allow_html=True)
                sec_hdr("Normalized Performance (Base=100)", "blue")
                st.markdown("<div style='margin-top: 0.8rem;'></div>", unsafe_allow_html=True)

                if True:
                    try:
                        st.plotly_chart(
                            create_comparison_chart(valid_syms, df),
                            use_container_width=True,
                            config={
                                "displayModeBar": False,
                                "scrollZoom": True,
                                "doubleClick": "reset+autosize",
                                "responsive": True,
                            }
                        )
                    except Exception as e:
                        logger.error("Comparison chart: %s", e)
                        st.warning("⚠️ Chart unavailable.")

                agent = get_agent()
                if agent and not st.session_state.agent_error:
                    with st.expander("🤖 AI Comparison Verdict", expanded=True):
                        if True:
                            try:
                                ai_sum = generate_comparison_summary(agent.llm, valid_syms, df.to_string(index=False), all_signals)
                            except Exception as e:
                                logger.error("AI compare: %s", e)
                                ai_sum = "⚠️ AI summary unavailable."
                        st.markdown(f'<div class="fin-card" style="line-height:1.75;font-size:0.9rem;color:var(--text); background: var(--surface); backdrop-filter: blur(16px); border: 1px solid var(--blue2); box-shadow: 0 0 20px rgba(14,165,233,0.15); border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem;">{ai_sum}</div>', unsafe_allow_html=True)
            else:
                st.error("❌ Could not fetch data. Check your symbols.")


# ═══════════════════════════════════════════════════════════
#  📰 NEWS & SENTIMENT
# ═══════════════════════════════════════════════════════════
elif page == "News & Sentiment":
    page_header("Market Intelligence", "News & Sentiment", "Real-time articles with VADER sentiment scoring")

    col_sym, col_btn = st.columns([4, 1])
    
    if st.session_state.get("selected_symbol") in ["BTC-USD", "RELIANCE.NS"]:
        st.session_state["selected_symbol"] = ""
        
    symbol_news = col_sym.text_input("Stock Symbol", value=st.session_state.get("selected_symbol",""), placeholder="e.g. RELIANCE.NS", label_visibility="collapsed")
    with col_btn:
        fetch_btn = st.button("📰 Fetch", type="primary", use_container_width=True)

    if fetch_btn:
        ok, norm = validate_symbol(symbol_news)
        if not ok:
            st.error(f"❌ {norm}"); st.stop()

        cname = norm
        try:
            p_info = get_stock_price(norm)
            cname  = p_info.get("company_name", norm) if "error" not in p_info else norm
        except: pass

        if True:
            try:    nr = get_news_with_sentiment(norm, cname)
            except Exception as e:
                logger.error("News: %s", e); st.error("⚠️ News unavailable."); nr = None

        if not nr: st.stop()

        # ── Layout: Gauge (left) | Stats + Summary (right) ──
        col_g, col_s = st.columns([1.5, 2.5])

        with col_g:
            sec_hdr(f"Sentiment — {cname.split()[0]}", "blue")
            st.plotly_chart(create_sentiment_gauge(nr["avg_score"]), use_container_width=True)
            sc_color = "#10B981" if nr["avg_score"] > 0.05 else ("#EF4444" if nr["avg_score"] < -0.05 else "#94A3C8")
            st.markdown(f"""
            <div class="fin-card" style="text-align:center;padding:0.9rem;">
              <div style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:800;color:{sc_color};">{nr["overall_sentiment"]}</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;color:{sc_color};margin-top:2px;">{nr["avg_score"]:+.3f}</div>
              <div style="font-size:0.68rem;color:var(--text3);margin-top:4px;">Avg Compound Score</div>
            </div>""", unsafe_allow_html=True)

        with col_s:
            sec_hdr("Breakdown", "blue")
            sb1, sb2, sb3 = st.columns(3)
            sb1.metric("📈 Positive", nr["pos_count"])
            sb2.metric("➡️ Neutral",  nr["neu_count"])
            sb3.metric("📉 Negative", nr["neg_count"])
            st.markdown(f'<div class="fin-card" style="border-left:3px solid var(--cyan);padding:0.9rem 1.1rem;font-size:0.84rem;color:var(--text2);line-height:1.6;margin-top:0.5rem;">{nr["summary"]}</div>', unsafe_allow_html=True)

        st.markdown("---")
        sec_hdr("Recent Articles", "blue")

        import html
        for art in nr["articles"]:
            sentiment = art.get("sentiment", {})
            score     = sentiment.get("compound", 0)
            if score > 0.05:
                cls = "pos"; badge_cls = "badge-green"; emoji = "📈"
            elif score < -0.05:
                cls = "neg"; badge_cls = "badge-red";   emoji = "📉"
            else:
                cls = "neu"; badge_cls = "badge-blue";  emoji = "➡️"

            title  = html.escape(art.get("title","Untitled"))[:120]
            desc   = html.escape(art.get("description",""))[:160]
            source = html.escape(art.get("source",""))
            pub    = html.escape(art.get("published_at",""))
            url    = art.get("url","#")
            label  = sentiment.get("label","Neutral ➡️").split()[0]

            st.markdown(f"""
            <div class="news-item {cls}">
              <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;">
                <a href="{url}" target="_blank"
                   style="font-weight:600;font-size:0.88rem;color:var(--text);text-decoration:none;flex:1;">{title}</a>
                <span class="badge {badge_cls}" style="flex-shrink:0;">{emoji} {label} ({score:+.2f})</span>
              </div>
              <div style="font-size:0.8rem;color:var(--text3);margin:0.4rem 0 0.6rem;line-height:1.45;">{desc}</div>
              <div style="display:flex;align-items:center;justify-content:space-between;">
                <span style="font-size:0.7rem;color:var(--text4);"><strong style="color:var(--text3);">{source}</strong> · {pub}</span>
                <a href="{url}" target="_blank" style="font-size:0.75rem;color:var(--blue2);font-weight:600;text-decoration:none;">Read article →</a>
              </div>
            </div>""", unsafe_allow_html=True)

        agent = get_agent()
        if agent and not st.session_state.agent_error:
            with st.expander("🤖 AI News Summary", expanded=False):
                from prompts import get_news_summary_prompt
                try:
                    articles_text = "\n".join([f"- {a.get('title','')} ({a.get('published_at','')})" for a in nr["articles"][:5]])
                    chain = get_news_summary_prompt() | agent.llm
                    if True:
                        resp = chain.invoke({"symbol": norm, "company_name": cname, "articles": articles_text,
                                            "sentiment_score": nr["avg_score"], "sentiment_label": nr["overall_sentiment"]})
                    resp_clean = resp.content.replace("**", "")
                    st.markdown(f'<div class="fin-card fin-card-glow-blue" style="line-height:1.75;font-size:0.88rem;color:var(--text2);">{resp_clean}</div>', unsafe_allow_html=True)
                except Exception as e:
                    logger.error("AI news: %s", e)
                    st.warning("⚠️ AI summary unavailable.")


# ═══════════════════════════════════════════════════════════
#  💼 PORTFOLIO TRACKER
# ═══════════════════════════════════════════════════════════
elif page == "Portfolio Tracker":
    page_header("Wealth Management", "Portfolio Tracker", "Live P&L · Risk Analysis · AI Insights")

    tab_view, tab_add = st.tabs(["📊 My Portfolio", "➕ Add Holding"])

    with tab_add:
        sec_hdr("Add New Holding", "green")
        fa1, fa2 = st.columns(2)
        p_sym  = fa1.text_input("Symbol",       placeholder="RELIANCE.NS")
        p_comp = fa2.text_input("Company Name", placeholder="Reliance Industries")
        fb1, fb2, fb3 = st.columns(3)
        p_qty  = fb1.number_input("Quantity",       min_value=1,    value=10)
        p_buy  = fb2.number_input("Buy Price (₹)",  min_value=0.01, value=1000.0, step=0.01)
        p_date = fb3.date_input("Buy Date")
        p_note = st.text_area("Notes (optional)", height=68)
        if st.button("➕ Add to Portfolio", type="primary"):
            if p_sym and p_buy > 0:
                ok, ns = validate_symbol(p_sym)
                if ok:
                    res = add_to_portfolio(ns, p_comp, float(p_buy), int(p_qty), str(p_date), p_note)
                    msg = str(res.get("message","Done"))
                    if res.get("success"):
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.error("❌ Invalid symbol")

    with tab_view:
        holdings = get_portfolio()
        if not holdings:
            st.info("📭 No holdings yet. Add in the ➕ tab.")
        else:
            if True:
                cur_px = {}
                for h in holdings:
                    try:
                        p = get_stock_price(h["symbol"])
                        cur_px[h["symbol"]] = p["current_price"] if "error" not in p else h["buy_price"]
                    except:
                        cur_px[h["symbol"]] = h["buy_price"]

            rows = []
            t_inv = t_cur = 0
            for h in holdings:
                sym = h["symbol"]
                inv = h["buy_price"] * h["quantity"]
                cur = cur_px[sym] * h["quantity"]
                pnl = cur - inv
                pct = (pnl/inv*100) if inv else 0
                t_inv += inv; t_cur += cur
                rows.append({"ID":h["id"],"Symbol":sym,"Company":h.get("company_name","")[:16],
                             "Qty":h["quantity"],"Buy ₹":f"{h['buy_price']:,.2f}","Now ₹":f"{cur_px[sym]:,.2f}",
                             "Invested ₹":f"{inv:,.0f}","Value ₹":f"{cur:,.0f}",
                             "P&L ₹":f"{pnl:+,.0f}","Return %":f"{pct:+.2f}%"})

            t_pnl = t_cur - t_inv
            t_pct = (t_pnl/t_inv*100) if t_inv else 0

            # Summary metrics
            st.markdown(f"""
            <div class="dash-metrics-grid">
              <div class="dash-metric-card">
                <div class="dash-metric-label">💰 Invested</div>
                <div class="dash-metric-value">₹{t_inv:,.0f}</div>
              </div>
              <div class="dash-metric-card">
                <div class="dash-metric-label">📈 Current Value</div>
                <div class="dash-metric-value">₹{t_cur:,.0f}</div>
              </div>
              <div class="dash-metric-card">
                <div class="dash-metric-label">💵 Total P&L</div>
                <div class="dash-metric-value">₹{t_pnl:+,.0f}</div>
                <div class="dash-metric-delta {'pos' if t_pct>=0 else 'neg'}">{'▲' if t_pct>=0 else '▼'} {abs(t_pct):.2f}%</div>
              </div>
              <div class="dash-metric-card">
                <div class="dash-metric-label">📋 Holdings</div>
                <div class="dash-metric-value">{len(holdings)}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            # Risk | Allocation | Returns
            col_r, col_p, col_ret = st.columns([1.2, 1.5, 1.5])

            with col_r:
                sec_hdr("Risk Score", "amber")
                if True:
                    try:    risk = calculate_portfolio_risk(holdings, cur_px)
                    except: risk = {"error": "Unavailable"}
                if "error" not in risk:
                    st.plotly_chart(create_risk_meter(risk["risk_score"]), use_container_width=True,
                                    config={"displayModeBar": False, "responsive": True})
                    rc = risk["risk_color"]
                    st.markdown(f"""
                    <div class="fin-card" style="text-align:center;padding:0.8rem;">
                      <div style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:800;color:{rc};">{risk["risk_label"]}</div>
                      <div style="font-size:0.75rem;color:var(--text3);margin-top:4px;line-height:1.5;">{risk["risk_description"]}</div>
                      <div style="font-size:0.68rem;color:var(--text4);margin-top:6px;">{risk.get("n_sectors",0)} sectors · {risk.get("n_holdings",0)} stocks · {risk.get("weighted_volatility",0):.1f}%/yr vol</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ {risk.get('error','Unavailable')}")

            with col_p:
                sec_hdr("Allocation", "blue")
                try:
                    pie_df = pd.DataFrame({"Symbol":[r["Symbol"] for r in rows],
                                           "Value (₹)":[h["buy_price"]*h["quantity"] for h in holdings]})
                    st.plotly_chart(create_portfolio_pie(pie_df), use_container_width=True,
                                    config={"displayModeBar": False, "responsive": True})
                except Exception as e:
                    logger.error("Pie: %s", e); st.info("Chart unavailable.")

            with col_ret:
                sec_hdr("Returns by Stock", "green")
                try:
                    st.plotly_chart(create_pnl_chart(rows), use_container_width=True,
                                    config={"displayModeBar": False, "scrollZoom": True, "doubleClick": "reset+autosize", "responsive": True})
                except Exception as e:
                    logger.error("PnL chart: %s", e); st.info("Chart unavailable.")

            st.markdown("---")
            sec_hdr("All Holdings", "blue")

            # Table rendered in one block to prevent Streamlit div interference
            table_html = '<div class="fin-card" style="padding:0; overflow:hidden;">'
            table_html += '<div class="scroll-container">'
            table_html += '<div class="holding-hdr"><div>Stock</div><div>Qty</div><div>Buy ₹</div><div>Now ₹</div><div>P&L ₹</div><div>Return</div><div></div></div>'
            for r in rows:
                pnl_color = "#10B981" if "+" in r["P&L ₹"] else "#EF4444"
                table_html += f"""
                <div class="holding-row">
                  <div>
                    <div style="font-family:'Outfit',sans-serif;font-weight:700;font-size:0.86rem;">{r["Symbol"].replace(".NS","")}</div>
                    <div style="font-size:0.67rem;color:var(--text3);">{r["Company"]}</div>
                  </div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;">{r["Qty"]}</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;">₹{r["Buy ₹"]}</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;">₹{r["Now ₹"]}</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;font-weight:700;color:{pnl_color};">{r["P&L ₹"]}</div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;font-weight:700;color:{pnl_color};">{r["Return %"]}</div>
                  <div></div>
                </div>"""
            table_html += '</div></div>'
            st.markdown(table_html, unsafe_allow_html=True)

            agent = get_agent()
            if agent and not st.session_state.agent_error:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🤖 AI Portfolio Analysis", key="portfolio_ai_btn_v2", type="primary"):
                    try:    result = agent.analyze_portfolio_with_ai(holdings, cur_px)
                    except: result = {"error": "Analysis error."}
                    if "error" not in result:
                        st.markdown(f'<div class="fin-card fin-card-glow-blue" style="line-height:1.75;font-size:0.88rem;color:var(--text2);">{result["ai_analysis"]}</div>', unsafe_allow_html=True)
                    else: st.error(f"❌ {result.get('error', 'Unavailable')}")

            st.markdown("---")
            sec_hdr("Remove Holding", "red")

            dc1, dc2 = st.columns([4, 1])
            hopts = {f"{r['Symbol']} · ID:{r['ID']}": r["ID"] for r in rows}
            sel   = dc1.selectbox("Select holding", list(hopts.keys()), index=None, placeholder="Select holding", label_visibility="collapsed")
            if dc2.button("Remove", key="rm_holding_btn_v2_final", type="secondary", use_container_width=True):
                if sel is not None:
                    res = remove_from_portfolio(hopts[sel])
                    if res["success"]: st.success(res["message"]); st.rerun()
                else:
                    st.warning("⚠️ Please select a holding to remove.")

# ═══════════════════════════════════════════════════════════
#  ⭐ WATCHLIST
# ═══════════════════════════════════════════════════════════
elif page == "Watchlist":
    page_header("TERMINAL", "Market Watchlist", "Professional High-Density Monitoring")

    # ── WATCHLIST CSS — Premium Terminal Design ────
    st.markdown("""
    <style>
    @keyframes wl-blink { 0%,100%{opacity:1} 50%{opacity:0.35} }

    /* ── LIVE BADGE ── */
    .wl-live-badge {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(14,165,233,0.07);
        border: 1px solid rgba(14,165,233,0.2);
        border-radius: 50px; padding: 6px 16px;
        font-family: "JetBrains Mono", monospace;
        font-size: 0.6rem; color: var(--blue2);
        font-weight: 600; letter-spacing: 0.12em;
        text-transform: uppercase; margin: 0 auto 1.2rem auto;
    }
    .wl-live-dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--blue); box-shadow: 0 0 8px var(--blue);
        animation: wl-blink 2s ease-in-out infinite; flex-shrink: 0;
    }

    /* ── WRAPPER ── */
    .wl-wrapper { max-width: 820px; }

    /* ── SHARED GRID ── */
    .wl-col-hdr,
    .wl-card-body {
        display: grid;
        grid-template-columns: 32px 1fr 110px 90px 75px;
        align-items: center;
        gap: 0 16px;
    }

    /* ── STICKY COLUMN HEADER ── */
    .wl-col-hdr {
        position: sticky; top: -1px; z-index: 100;
        background: #09090b; /* Match terminal background */
        padding: 12px 20px 8px 20px;
        margin: 0 auto 6px auto;
        border-bottom: 1px solid var(--border);
        max-width: 820px;
    }
    .wl-col-hdr span {
        display: block; width: 100%;
        font-family: "JetBrains Mono", monospace;
        font-size: 0.5rem; color: var(--text4);
        text-transform: uppercase; letter-spacing: 0.16em; font-weight: 700;
    }
    .wl-col-hdr span:nth-child(1) { text-align: center; }
    .wl-col-hdr span:nth-child(2) { text-align: left; }
    .wl-col-hdr span:nth-child(3),
    .wl-col-hdr span:nth-child(4) { text-align: right; }
    .wl-col-hdr span:nth-child(5) { text-align: center; }
    @media (max-width: 640px) { .wl-col-hdr { display: none; } }

    /* ── CARD ── */
    .wl-card {
        position: relative; overflow: hidden;
        background: linear-gradient(135deg, rgba(24,24,27,0.9) 0%, rgba(18,18,24,0.95) 100%);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.07);
        border-top: 1px solid rgba(255,255,255,0.11);
        border-radius: 14px;
        margin: 0 auto 10px auto;
        max-width: 820px;
        transition: all 0.22s cubic-bezier(0.4,0,0.2,1);
        box-shadow: 0 2px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    }
    .wl-card::before {
        content: \'\'; position: absolute; inset: 0;
        background: linear-gradient(105deg, rgba(255,255,255,0.025) 0%, transparent 50%);
        pointer-events: none; z-index: 0; border-radius: 14px;
    }
    .wl-card::after {
        content: \'\'; position: absolute;
        left: 0; top: 8px; bottom: 8px; width: 3px; z-index: 1;
        background: var(--wl-accent, var(--blue));
        box-shadow: 0 0 16px var(--wl-accent, var(--blue));
        border-radius: 0 3px 3px 0;
    }
    .wl-card:hover {
        border-color: rgba(255,255,255,0.16);
        transform: translateY(-2px) scale(1.002);
        box-shadow: 0 8px 32px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.06), inset 0 1px 0 rgba(255,255,255,0.08);
        background: linear-gradient(135deg, rgba(30,30,38,0.95) 0%, rgba(22,22,30,0.98) 100%);
    }
    .wl-card:hover::after { box-shadow: 0 0 24px var(--wl-accent, var(--blue)); }

    /* ── CARD BODY ── */
    .wl-card-body {
        position: relative; z-index: 2;
        padding: 14px 20px 14px 22px;
    }

    /* ── RANK ── */
    .wl-rank {
        font-family: "JetBrains Mono", monospace;
        font-size: 0.55rem; font-weight: 600;
        color: var(--text4); text-align: center;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 6px; padding: 3px 0;
    }

    /* ── IDENTITY ── */
    .wl-id { min-width: 0; overflow: hidden; }
    .wl-sym {
        font-family: "Outfit", sans-serif;
        font-size: 1.05rem; font-weight: 800; color: #fff;
        letter-spacing: -0.4px; line-height: 1.1;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .wl-name-sub {
        font-family: "JetBrains Mono", monospace;
        font-size: 0.6rem; color: var(--text4);
        margin-top: 3px; letter-spacing: 0.03em;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }

    /* ── PRICE & CHANGE columns ── */
    .wl-price-block { text-align: right; }
    .wl-price {
        font-family: "JetBrains Mono", monospace;
        font-size: 0.95rem; font-weight: 700; color: #fff;
        letter-spacing: -0.5px; line-height: 1.2; white-space: nowrap;
    }
    .wl-chg {
        font-family: "JetBrains Mono", monospace;
        font-size: 0.68rem; font-weight: 700;
        margin-top: 3px; white-space: nowrap; text-align: right;
    }

    /* ── SIGNAL ── */
    .wl-sig-wrap { text-align: center; }
    .wl-sig {
        display: inline-flex; align-items: center; justify-content: center;
        font-family: "JetBrains Mono", monospace;
        font-size: 0.58rem; font-weight: 800; letter-spacing: 0.1em;
        padding: 5px 0; border-radius: 8px; white-space: nowrap;
        width: 100%; min-width: 52px;
        transition: box-shadow 0.2s;
    }
    .wl-card:hover .wl-sig { box-shadow: 0 0 16px var(--wl-accent, var(--blue)); }

    /* ── SPACER/MOBILE HELPERS ── */
    .wl-spacer { display: none; }
    .wl-name-mobile { display: none; }

    /* ── EMPTY STATE ── */
    .wl-empty {
        background: var(--surface); border: 1px dashed rgba(255,255,255,0.08);
        border-radius: var(--r16); padding: 3.5rem 1.5rem;
        text-align: center; margin: 0 auto 1rem auto; max-width: 820px;
    }
    .wl-empty-icon { font-size: 2.2rem; opacity: 0.4; margin-bottom: 0.8rem; }
    .wl-empty-text {
        font-family: "JetBrains Mono", monospace;
        font-size: 0.72rem; color: var(--text4);
        text-transform: uppercase; letter-spacing: 0.1em; line-height: 1.8;
    }

    /* ── MOBILE ── */
    @media (max-width: 640px) {
        .wl-wrapper { max-width: 100%; }
        .wl-card { max-width: 100%; }
        .wl-col-hdr { display: none; }
        .wl-card-body {
            grid-template-columns: 16px 1fr 62px 52px 40px;
            padding: 7px 6px;
            gap: 0 3px;
        }
        .wl-sym { font-size: 0.78rem; }
        .wl-rank { font-size: 0.45rem; width: 16px; padding: 2px 0; }
        .wl-price { font-size: 0.78rem; }
        .wl-chg { font-size: 0.58rem; }
        .wl-sig { font-size: 0.5rem; min-width: 38px; padding: 4px 0; }
        .wl-name-sub { font-size: 0.5rem; margin-top: 1px; }
    }
    </style>
    """, unsafe_allow_html=True)

    # ── ACTION SECTION (ADD) ───────────────────────────
    def render_watchlist_add_logic():
        with st.expander("➕ Add New Asset", expanded=False):
            with st.form("wl_add_form", clear_on_submit=True):
                ca1, ca2 = st.columns([1.2, 2.2])
                with ca1:
                    sym_in = st.text_input("Symbol", placeholder="RELIANCE.NS", label_visibility="collapsed").upper().strip()
                with ca2:
                    note_in = st.text_input("Note (optional)", placeholder="e.g. Long-term", label_visibility="collapsed")
                
                submit_btn = st.form_submit_button("Add to Watchlist ➕", type="primary", use_container_width=True)
                
                if submit_btn:
                    if sym_in:
                        with st.spinner("Validating..."):
                            ok, norm = validate_symbol(sym_in)
                            if ok:
                                p  = get_stock_price(norm)
                                cn = p.get("company_name", norm) if "error" not in p else norm
                                res = add_to_watchlist(norm, cn, note_in)
                                if res["success"]:
                                    st.rerun()
                                else:
                                    st.error(res["message"])
                            else:
                                st.error("❌ Invalid symbol")
                    else:
                        st.warning("Symbol required.")

    render_watchlist_add_logic()

    st.markdown("<br>", unsafe_allow_html=True)

    def render_watchlist_fragment():
        watchlist = get_watchlist()

        if not watchlist:
            st.markdown("""
            <div class="wl-empty">
              <div class="wl-empty-icon">📭</div>
              <div class="wl-empty-text">Watchlist is empty<br>
                <span style="color:var(--text4);font-size:0.65rem;">Add assets below to start monitoring</span>
              </div>
            </div>""", unsafe_allow_html=True)
            return

        symbols = [item["symbol"] for item in watchlist]
        with st.spinner("Syncing terminal..."):
            prices = batch_fetch_prices(symbols)



        # Desktop column headers
        st.markdown("""
        <div class="wl-col-hdr">
          <span>#</span><span>Symbol</span>
          <span>Price</span><span>Change</span><span>Signal</span>
        </div>""", unsafe_allow_html=True)

        # ── One card per watchlist item ───────────────────────
        for idx, item in enumerate(watchlist):
            s      = item["symbol"]
            p_data = prices.get(s, {"current_price": 0, "change_pct": 0})
            px     = p_data.get("current_price", 0)
            chg    = p_data.get("change_pct", 0)
            name   = item.get("company_name", s)

            px_txt    = f"₹{px:,.2f}" if px else "—"
            chg_txt   = f"{chg:+.2f}%"
            trend_ico = "▲" if chg >= 0 else "▼"
            sym_short  = s.replace(".NS", "").replace(".BO", "")
            name_short = name[:28]

            sig     = "BUY"  if chg > 1.0 else ("SELL" if chg < -1.0 else "HOLD")
            sig_raw = "#10B981" if sig == "BUY" else ("#EF4444" if sig == "SELL" else "#F59E0B")

            st.markdown(f"""
            <div class="wl-card" style="--wl-accent:{sig_raw};">
              <div class="wl-card-body">
                <div class="wl-rank">{idx+1:02d}</div>
                <div class="wl-id">
                  <div class="wl-sym">{sym_short}</div>
                  <div class="wl-name-sub">{name_short}</div>
                </div>
                <div class="wl-price-block">
                  <div class="wl-price">{px_txt}</div>
                </div>
                <div class="wl-price-block">
                  <div class="wl-chg" style="color:{sig_raw};">{trend_ico} {chg_txt}</div>
                </div>
                <div class="wl-sig-wrap">
                  <span class="wl-sig" style="background:{sig_raw}12;color:{sig_raw};border:1px solid {sig_raw}30;">{sig}</span>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    # Apply fragment decorator
    if hasattr(st, "fragment"):
        render_watchlist_fragment = st.fragment()(render_watchlist_fragment)

    render_watchlist_fragment()

    # ── ACTION SECTION (ADD/REMOVE) ───────────────────────────
    def render_watchlist_actions_logic():
        # Remove Section
        wl = get_watchlist()
        if wl:
            st.markdown("<br>", unsafe_allow_html=True)
            sec_hdr("Remove Asset", "red")
            rm_opts = {f"{item['symbol'].replace('.NS','').replace('.BO','')} · {item['symbol']}": item["symbol"] for item in wl}
            rc1, rc2 = st.columns([4, 1])
            rm_sel = rc1.selectbox("Select asset to remove", list(rm_opts.keys()), index=None, placeholder="Select stock", key="wl_rm_sel_stable", label_visibility="collapsed")
            if rc2.button("Remove", key="wl_rm_btn_stable", type="secondary", use_container_width=True):
                if rm_sel is not None:
                    res = remove_from_watchlist(rm_opts[rm_sel])
                    if res.get("success"):
                        st.toast(f"🗑️ {rm_sel.split(' ·')[0]} removed", icon="✅")
                        time.sleep(0.2); st.rerun()
                    else: st.toast(f"⚠️ {res.get('message','Failed')}", icon="⚠️")
                else:
                    st.warning("⚠️ Please select an asset to remove.")


    render_watchlist_actions_logic()










# ═══════════════════════════════════════════════════════════
#  📋 MARKET BRIEF
# ═══════════════════════════════════════════════════════════
elif page == "Market Brief":
    page_header("Daily Digest", "AI Market Brief", "AI-generated market summary with movers & macro context")

    st.markdown("---")

    if True:
        try:    nifty  = get_stock_price("^NSEI")
        except: nifty  = {"error":"Unavailable"}
        try:    sensex = get_stock_price("^BSESN")
        except: sensex = {"error":"Unavailable"}
        try:    mood   = get_market_mood()
        except: mood   = {"mood_label":"Neutral ➡️","mood_color":"#F59E0B","mood_score":50,"bullish_pct":40,"neutral_pct":35,"bearish_pct":25}
        try:    movers = get_top_movers()
        except: movers = {"gainers":[],"losers":[]}

    # Indices row
    col_n, col_s, col_m = st.columns(3)
    with col_n:
        sec_hdr("Nifty 50", "blue")
        if "error" not in nifty:
            cc = "#10B981" if nifty["change_pct"] >= 0 else "#EF4444"
            arrow = "▲" if nifty["change_pct"] >= 0 else "▼"
            cls   = "green-top" if nifty["change_pct"] >= 0 else "red-top"
            st.markdown(f"""
            <div class="idx-pill {cls}">
              <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:var(--text);letter-spacing:-1px;">{nifty['current_price']:,.2f}</div>
              <div style="font-size:1rem;color:{cc};font-weight:700;margin-top:3px;">{arrow} {abs(nifty['change_pct']):.2f}%</div>
              <div style="font-size:0.65rem;color:var(--text3);margin-top:3px;">Prev: ₹{nifty.get('previous_close',0):,.2f}</div>
            </div>""", unsafe_allow_html=True)

    with col_s:
        sec_hdr("Sensex", "amber")
        if "error" not in sensex:
            cc = "#10B981" if sensex["change_pct"] >= 0 else "#EF4444"
            arrow = "▲" if sensex["change_pct"] >= 0 else "▼"
            cls   = "green-top" if sensex["change_pct"] >= 0 else "red-top"
            st.markdown(f"""
            <div class="idx-pill {cls}">
              <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:800;color:var(--text);letter-spacing:-1px;">{sensex['current_price']:,.2f}</div>
              <div style="font-size:1rem;color:{cc};font-weight:700;margin-top:3px;">{arrow} {abs(sensex['change_pct']):.2f}%</div>
              <div style="font-size:0.65rem;color:var(--text3);margin-top:3px;">Prev: ₹{sensex.get('previous_close',0):,.2f}</div>
            </div>""", unsafe_allow_html=True)

    with col_m:
        sec_hdr("Market Mood", "blue")
        st.plotly_chart(create_market_mood_chart(mood["mood_score"]), use_container_width=True)

    st.markdown("---")

    # ── MARKET BREADTH METER ─────────────────────────────────
    try:
        breadth = get_market_breadth()
    except:
        breadth = {"advance": 0, "decline": 0, "unchanged": 0, "total": 1, "ad_ratio": 0.0, "avg_change": 0.0, "breadth_label": "Unknown", "breadth_color": "#888"}

    cb1, cb2 = st.columns([1.5, 1])
    with cb1:
        sec_hdr("Market Breadth Meter", "blue")
        st.markdown(f"""
        <div class="fin-card">
          <div style="font-size:0.85rem;color:var(--text2);margin-bottom:8px;font-weight:600;">{breadth['breadth_label']}</div>
          <div style="display:flex;height:12px;border-radius:6px;overflow:hidden;margin-bottom:12px;">
            <div style="width:{(breadth['advance']/breadth['total'])*100}%;background:#10B981;"></div>
            <div style="width:{(breadth['unchanged']/breadth['total'])*100}%;background:#F59E0B;"></div>
            <div style="width:{(breadth['decline']/breadth['total'])*100}%;background:#EF4444;"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-family:'JetBrains Mono',monospace;font-size:0.75rem;">
            <span style="color:#10B981;">{breadth['advance']} Adv</span>
            <span style="color:#F59E0B;">{breadth['unchanged']} Unc</span>
            <span style="color:#EF4444;">{breadth['decline']} Dec</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with cb2:
        sec_hdr("A/D Ratio", "amber")
        st.markdown(f"""
        <div class="fin-card" style="text-align:center;padding:1.5rem 1rem;">
          <div style="font-family:'Outfit',sans-serif;font-size:2.2rem;font-weight:800;color:{breadth['breadth_color']};line-height:1;">{breadth['ad_ratio']}</div>
          <div style="font-size:0.7rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em;margin-top:6px;">Advance/Decline</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── SECTOR PERFORMANCE TILES ─────────────────────────────
    try:
        heatmap_data = get_sector_heatmap()
    except:
        heatmap_data = []

    sec_hdr("Sector Performance Tiles", "purple")
    if heatmap_data:
        tile_cols = st.columns(min(len(heatmap_data), 5))
        for i, sec in enumerate(heatmap_data[:5]):
            with tile_cols[i]:
                c = "#10B981" if sec["avg_change"] >= 0 else "#EF4444"
                arrow = "▲" if sec["avg_change"] >= 0 else "▼"
                st.markdown(f"""
                <div class="idx-pill" style="padding:0.7rem;text-align:center;">
                  <div style="font-size:0.7rem;color:var(--text2);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{sec['sector']}</div>
                  <div style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:700;color:{c};">{arrow} {abs(sec['avg_change']):.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No sector data available.")

    st.markdown("---")

    st.markdown("<br>", unsafe_allow_html=True)
    gen_btn = st.button("⚡ Generate Today's Brief", type="primary", use_container_width=True)

    if gen_btn:
        agent = get_agent()
        if agent and not st.session_state.agent_error:
            if True:
                try:
                    mn   = get_news_with_sentiment("NIFTY","Indian stock market")
                    hdls = "\n".join([f"- {a['title']}" for a in mn.get("articles",[])[:6]]) or "No headlines"
                except:
                    hdls = "News unavailable"
                try:
                    brief = generate_market_brief(agent.llm,
                        nifty  if "error" not in nifty  else {},
                        sensex if "error" not in sensex else {},
                        heatmap_data, breadth,
                        hdls, mood["mood_label"])
                except Exception as e:
                    logger.error("Brief: %s", e)
                    brief = "⚠️ Brief generation failed."

            st.markdown("---")
            sec_hdr("AI Brief", "blue")
            st.markdown(f'<div class="fin-card fin-card-glow-blue" style="line-height:1.8;font-size:0.9rem;color:var(--text2);">{brief}</div>', unsafe_allow_html=True)
        else:
            st.error("⚠️ LLM API key not configured.")


# ═══════════════════════════════════════════════════════════
#  🧮 CALCULATORS
# ═══════════════════════════════════════════════════════════
elif page == "Calculators":
    page_header("Financial Tools", "Calculators", "SIP projection · Capital gains tax estimator")

    calc_options = ["💰 SIP Calculator", "🏛️ Capital Gains Tax"]
    calc_type = st.selectbox("Calculator Type", calc_options, label_visibility="collapsed")


    if calc_type == "💰 SIP Calculator":
        sec_hdr("SIP Return Calculator", "green")

        # Inputs
        ci1, ci2, ci3 = st.columns(3)
        monthly_sip   = ci1.number_input("Monthly SIP (₹)", min_value=100, value=5000, step=500)
        annual_return = ci2.slider("Expected Return (%)", 4.0, 25.0, 12.0, 0.5)
        years         = ci3.slider("Duration (Years)",    1,   30,   10)

        if st.button("📊 Calculate Returns", type="primary"):
            result = calculate_sip(monthly_sip, annual_return, years)
            sr1, sr2, sr3, sr4 = st.columns(4)
            sr1.metric("💰 Monthly SIP",   f"₹{monthly_sip:,.0f}")
            sr2.metric("📊 Total Invested", f"₹{result['total_invested']:,.0f}")
            sr3.metric("📈 Future Value",   f"₹{result['estimated_returns']:,.0f}")
            sr4.metric("🤑 Wealth Gained",  f"₹{result['wealth_gained']:,.0f}", f"+{result['absolute_return_pct']:.1f}%")

            st.plotly_chart(create_sip_chart(result["yearly_breakdown"]), use_container_width=True)

            with st.expander("📋 Year-by-Year Breakdown"):
                bdf = pd.DataFrame(result["yearly_breakdown"])
                bdf.columns = ["Year","Invested (₹)","Value (₹)"]
                bdf["Gain (₹)"] = bdf["Value (₹)"] - bdf["Invested (₹)"]
                bdf["Return %"] = (bdf["Gain (₹)"] / bdf["Invested (₹)"] * 100).round(2)
                st.dataframe(bdf, use_container_width=True, hide_index=True)

    else:
        sec_hdr("Capital Gains Tax Calculator", "amber")
        st.caption("LTCG (12.5%) applies after 1 year · STCG (20%) for ≤1 year — as per Indian tax law")
        tc1, tc2, tc3, tc4 = st.columns(4)
        buy_pt       = tc1.number_input("Buy Price (₹)",  min_value=1.0, value=500.0)
        sell_pt      = tc2.number_input("Sell Price (₹)", min_value=1.0, value=700.0)
        qty_t        = tc3.number_input("Quantity",       min_value=1,   value=100)
        holding_days = tc4.number_input("Holding Days",   min_value=1,   value=400)

        if st.button("🧮 Calculate Tax", type="primary"):
            tax = calculate_tax_implications(buy_pt, sell_pt, qty_t, holding_days)
            tr1, tr2, tr3 = st.columns(3)
            tr1.metric("💰 Investment", f"₹{tax['total_investment']:,.2f}")
            tr2.metric("📈 Proceeds",   f"₹{tax['total_proceeds']:,.2f}")
            tr3.metric("💵 Gross Gain", f"₹{tax['gross_gain_loss']:+,.2f}", f"{tax['return_pct']:+.2f}%")

            is_lt  = "LTCG" in tax["tax_type"]
            t_bdr  = "#F59E0B" if is_lt else "#EF4444"
            t_bg   = "rgba(245,158,11,0.06)" if is_lt else "rgba(239,68,68,0.06)"
            t_cls  = "fin-card-glow-amber" if is_lt else "fin-card-glow-red"

            st.markdown(f"""
            <div class="fin-card {t_cls}" style="margin-top:0.75rem;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.9rem;">
                <span style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:800;color:{t_bdr};">📋 {tax["tax_type"]}</span>
                <span class="badge {'badge-amber' if is_lt else 'badge-red'}">{holding_days} days · {tax["tax_rate_pct"]}% rate</span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:1.1rem;">
                <div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.58rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Tax Payable</div>
                  <div style="font-family:'Outfit',sans-serif;font-size:1.6rem;font-weight:800;color:#EF4444;">₹{tax["tax_payable"]:,.2f}</div>
                </div>
                <div>
                  <div style="font-family:'JetBrains Mono',monospace;font-size:0.58rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Net Gain After Tax</div>
                  <div style="font-family:'Outfit',sans-serif;font-size:1.6rem;font-weight:800;color:#10B981;">₹{tax["net_gain_after_tax"]:,.2f}</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
            st.caption("⚠️ Approximate. Consult a CA for accurate computation.")


# ═══════════════════════════════════════════════════════════
#  🤖 AI CHAT  ─  NEW PREMIUM DESIGN
# ═══════════════════════════════════════════════════════════
elif page == "AI Chat":

    # ── Page Header ───────────────────────────────────────
    page_header("Intelligent Assistant", "FinSaarthi AI", "Ask anything about Indian stocks, markets & investing")

    # ── Status Bar ────────────────────────────────────────
    agent_ok = not st.session_state.agent_error
    status_color = "#10B981" if agent_ok else "#EF4444"
    status_label = "AI Ready · Connected" if agent_ok else "LLM Not Configured"
    history_count = len(st.session_state.chat_history)

    st.markdown(f"""
    <div class="chat-status-bar">
      <div style="display:flex;align-items:center;gap:10px;">
        <div class="chat-status-dot" style="background:{status_color};box-shadow:0 0 8px {status_color};"></div>
        <span style="font-size:0.75rem;font-weight:600;color:{'#34D399' if agent_ok else '#F87171'};">{status_label}</span>
        <span style="font-size:0.7rem;color:var(--text4);">·</span>
        <span style="font-size:0.7rem;color:var(--text3);">FinSaarthi AI v2.0</span>
      </div>
      <div style="display:flex;align-items:center;gap:16px;">
        <span style="font-size:0.72rem;color:var(--text4);">{history_count // 2} conversation{'s' if history_count // 2 != 1 else ''}</span>
        <div style="display:flex;align-items:center;gap:5px;">
          <div style="width:5px;height:5px;border-radius:50%;background:var(--blue);"></div>
          <span style="font-size:0.7rem;color:var(--text4);">Powered by LangChain</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.agent_error:
        st.error(f"⚠️ LLM Not Configured: {st.session_state.agent_error}")

    # ── Chat History Display ──────────────────────────────
    import datetime as _dt

    if st.session_state.chat_history:
        chat_html = '<div class="chat-scroll-area">'
        for idx, msg in enumerate(st.session_state.chat_history):
            is_user = msg["role"] == "user"
            bubble_cls = "user-bubble" if is_user else "ai-bubble"
            wrap_cls   = "user-wrap"   if is_user else ""
            avatar_cls = "user-avatar" if is_user else "ai-avatar"
            avatar_icon = "U" if is_user else "📈"
            raw = str(msg["content"])
            if not is_user:
                import re
                # Convert markdown to HTML for AI messages
                raw = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', raw)
                raw = re.sub(r'\*(.+?)\*', r'<em>\1</em>', raw)
                raw = re.sub(r'^### (.+)$', r'<h4 style="margin:0.6rem 0 0.2rem;color:var(--text)">\1</h4>', raw, flags=re.MULTILINE)
                raw = re.sub(r'^## (.+)$',  r'<h3 style="margin:0.6rem 0 0.2rem;color:var(--text)">\1</h3>', raw, flags=re.MULTILINE)
                raw = re.sub(r'^# (.+)$',   r'<h2 style="margin:0.6rem 0 0.2rem;color:var(--text)">\1</h2>', raw, flags=re.MULTILINE)
                
                # Wrap lists correctly
                if "- " in raw:
                    def wrap_list(m):
                        inner = re.sub(r"^- (.+)$", r"<li>\1</li>", m.group(0), flags=re.MULTILINE)
                        return '<ul style="margin:0.5rem 0;padding-left:1.2rem;">' + inner + '</ul>'
                    raw = re.sub(r'(?:^- .+(?:\n|$))+', wrap_list, raw, flags=re.MULTILINE)
                
                raw = raw.replace('\n', '<br>')
                # Clean up artifacts
                raw = raw.replace('</ul><br>', '</ul>')
                raw = raw.replace('</li><br>', '</li>')
                for h in range(1, 5):
                    raw = raw.replace(f'</h{h}><br>', f'</h{h}>')
                content = raw
            else:
                content = raw.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
            
            # Calculate dynamic timestamp
            import time
            ts = msg.get("timestamp", time.time())
            diff = int(time.time() - ts)
            if diff < 60:
                time_str = "just now"
            elif diff < 3600:
                mins = diff // 60
                time_str = f"{mins} min{'s' if mins > 1 else ''} ago"
            elif diff < 86400:
                hrs = diff // 3600
                time_str = f"{hrs} hr{'s' if hrs > 1 else ''} ago"
            else:
                days = diff // 86400
                time_str = f"{days} day{'s' if days > 1 else ''} ago"

            chat_html += f"""
            <div class="chat-msg-wrap {wrap_cls}">
              <div class="chat-avatar {avatar_cls}">{avatar_icon}</div>
              <div>
                <div class="chat-bubble {bubble_cls}">{content}</div>
                <div class="chat-meta">{'You' if is_user else 'FinSaarthi AI'} · {time_str}</div>
              </div>
            </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

    # ── Input Row ─────────────────────────────────────────
    prefill = st.session_state.pop("prefill_q", "")

    st.markdown('<div class="chat-input-row">', unsafe_allow_html=True)
    inp_col, btn_col = st.columns([9, 1])
    with inp_col:
        typed = st.text_input(
            label="chat_input_hidden",
            label_visibility="collapsed",
            placeholder="Ask about stocks, markets, SIP, tax, investing…",
            key="chat_input_box",
            value=prefill if prefill else st.session_state.get("_chat_draft", ""),
        )
    with btn_col:
        send_clicked = st.button("➤", key="chat_send_btn", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    user_input = typed if send_clicked else None

    if (user_input and send_clicked) or prefill:
        q = (user_input or prefill).strip()
        # Clear input box after send
        st.session_state["_chat_draft"] = ""
        import time
        st.session_state.chat_history.append({"role": "user", "content": q, "timestamp": time.time()})
        agent = get_agent()
        if agent:
            if True:
                st.markdown("""
                <div style="display:flex;align-items:center;gap:8px;padding:0.5rem 0 0.8rem;">
                  <div style="font-size:0.78rem;color:var(--text3);">FinSaarthi AI is thinking</div>
                  <span class="typing-dot"></span>
                  <span class="typing-dot"></span>
                  <span class="typing-dot"></span>
                </div>
                """, unsafe_allow_html=True)
                try:
                    resp = agent.chat(q)
                except Exception as e:
                    logger.error("Chat: %s", e)
                    resp = "⚠️ Error processing your question. Please try again."
        else:
            resp = "⚠️ LLM not configured. Please add your API key in `.env` to enable AI responses."
        st.session_state.chat_history.append({"role": "assistant", "content": resp, "timestamp": time.time()})
        st.rerun()

    # ── Action Row ────────────────────────────────────────
    if st.session_state.chat_history:
        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        col_clr, col_exp, col_info = st.columns([1, 2, 3])
        with col_clr:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                if st.session_state.agent:
                    st.session_state.agent.clear_memory()
                st.rerun()
        with col_exp:
            # ── Generate Modern PDF ──────────────────────────
            def generate_chat_pdf(history):
                import io, re, datetime
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.lib.units import mm
                from reportlab.lib.styles import ParagraphStyle
                from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
                from reportlab.platypus import (
                    SimpleDocTemplate, Paragraph, Spacer,
                    HRFlowable, Table, TableStyle, KeepTogether
                )
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                from reportlab.pdfgen import canvas as pdfcanvas

                # Register Arial (Unicode — supports ₹)
                try:
                    pdfmetrics.registerFont(TTFont("Arial",    "C:/Windows/Fonts/arial.ttf"))
                    pdfmetrics.registerFont(TTFont("ArialBd",  "C:/Windows/Fonts/arialbd.ttf"))
                    pdfmetrics.registerFont(TTFont("ArialIt",  "C:/Windows/Fonts/ariali.ttf"))
                    BASE, BOLD, ITALIC = "Arial", "ArialBd", "ArialIt"
                except Exception:
                    BASE, BOLD, ITALIC = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"

                # ── Colour palette ──────────────────────────
                BG        = colors.HexColor("#0A0F1E")
                ACCENT    = colors.HexColor("#10B981")   # green
                USER_C    = colors.HexColor("#6366F1")   # indigo
                AI_C      = colors.HexColor("#10B981")
                USER_BG   = colors.HexColor("#1E1B4B")
                AI_BG     = colors.HexColor("#0F1929")
                TEXT_MAIN = colors.HexColor("#E2E8F0")
                TEXT_SUB  = colors.HexColor("#94A3B8")
                LINE_C    = colors.HexColor("#1E3A5F")
                WHITE     = colors.HexColor("#FFFFFF")

                W, H = A4
                LM, RM, TM, BM = 18*mm, 18*mm, 22*mm, 22*mm
                PW = W - LM - RM  # printable width

                # ── Helper: strip markdown ──────────────────
                def clean(text):
                    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
                    text = re.sub(r'\*(.+?)\*',     r'\1', text)
                    text = re.sub(r'^#{1,3} ',       '',   text, flags=re.MULTILINE)
                    text = re.sub(r'<[^>]+>',        '',   text)
                    text = re.sub(r'-{2,}',          '—',  text)
                    return text.strip()

                # ── Canvas callback for recurring footer/page numbers ──
                class HeaderFooter:
                    def __init__(self):
                        self.ts = datetime.datetime.now().strftime("%d %b %Y · %I:%M %p")
                    def __call__(self, canv, doc):
                        canv.saveState()
                        pg = doc.page
                        # Minimal recurring header for subsequent pages
                        if pg > 1:
                            canv.setFillColor(colors.HexColor("#080C16"))
                            canv.rect(0, H - 12*mm, W, 12*mm, fill=1, stroke=0)
                            canv.setFont(BOLD, 9)
                            canv.setFillColor(WHITE)
                            canv.drawString(LM, H - 8*mm, "FinSaarthi AI")
                            canv.setFont(BASE, 7)
                            canv.setFillColor(colors.HexColor("#94A3B8"))
                            canv.drawRightString(W - RM, H - 8*mm, f"Continued · {self.ts}")

                        # Recurring Footer
                        canv.setFont(BASE, 7)
                        canv.setFillColor(colors.HexColor("#64748B"))
                        canv.drawCentredString(W/2, BM - 8*mm,
                            "Confidential AI Analysis · FinSaarthi Insights · Not SEBI registered advice")
                        canv.setFont(BOLD, 7.5)
                        canv.setFillColor(ACCENT)
                        canv.drawRightString(W - RM, BM - 8*mm, f"PAGE {pg}")
                        canv.restoreState()

                hf = HeaderFooter()

                buf = io.BytesIO()
                doc = SimpleDocTemplate(
                    buf, pagesize=A4,
                    leftMargin=LM, rightMargin=RM,
                    topMargin=20*mm, bottomMargin=BM + 6*mm,
                    onFirstPage=hf, onLaterPages=hf,
                )

                # ── Styles ──────────────────────────────────
                def S(name, **kw):
                    defaults = dict(fontName=BASE, fontSize=9.5, textColor=TEXT_MAIN, leading=15)
                    defaults.update(kw)
                    return ParagraphStyle(name, **defaults)

                sTitleMain = S("stm", fontSize=22, fontName=BOLD, textColor=WHITE, alignment=TA_LEFT)
                sTitleSub  = S("sts", fontSize=8,  fontName=BASE, textColor=colors.HexColor("#94A3B8"), alignment=TA_RIGHT)
                sBadge     = S("sbd", fontSize=6,  fontName=BOLD, textColor=colors.HexColor("#93C5FD"), alignment=TA_CENTER)
                sLabel     = S("lbl", fontSize=7.5, fontName=BOLD, spaceAfter=2)
                sUser   = S("utx",  textColor=colors.HexColor("#C7D2FE"), spaceAfter=0)
                sAI     = S("aitx", textColor=colors.HexColor("#D1FAE5"), spaceAfter=0)
                sHead   = S("hd",   fontSize=10,  fontName=BOLD, textColor=WHITE, spaceAfter=1, spaceBefore=4)
                sBullet = S("bl",   leftIndent=8, spaceAfter=1, bulletIndent=2)

                def parse_ai(text):
                    """Convert markdown lines → Paragraphs with robust tag handling."""
                    import html
                    items = []
                    for line in text.splitlines():
                        line = line.strip()
                        if not line:
                            items.append(Spacer(1, 2))
                            continue
                        
                        # 1. HTML Escape to prevent literal < or > from breaking ReportLab
                        t = html.escape(line)
                        
                        # 2. Match headers
                        hm = re.match(r'^#{1,3}\s+(.*)', t)
                        if hm:
                            inner = hm.group(1)
                            inner = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', inner)
                            items.append(Paragraph(inner, sHead))
                            continue
                            
                        # 3. Match bullets
                        bm = re.match(r'^[-•]\s+(.*)', t)
                        if bm:
                            inner = bm.group(1)
                            inner = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', inner)
                            items.append(Paragraph(f"• {inner}", sBullet))
                            continue
                            
                        # 4. Normal text with bold/italic
                        t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
                        t = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', t)
                        
                        # Final check for balanced tags to avoid ReportLab ValueError
                        # If tags are unbalanced (e.g. <b> without </b>), Paragraph() will still fail.
                        # We try to build it, and if it fails, we fall back to raw escaped text.
                        try:
                            items.append(Paragraph(t, sAI))
                        except Exception:
                            items.append(Paragraph(html.escape(line), sAI))
                    return items

                # ── Build story ──────────────────────────────
                story = []
                
                # ── Bulletproof Branding Header ───────────────
                # Using a Table instead of Canvas for 100% reliability
                branding_data = [
                    [
                        Paragraph(f"<font color='#FFFFFF'>Fin</font><font color='#10B981'>Saarthi AI</font>", sTitleMain),
                        Paragraph(f"CONVERSATION REPORT<br/>Generated: {datetime.datetime.now().strftime('%d %b %Y · %I:%M %p')}", sTitleSub)
                    ]
                ]
                brand_t = Table(branding_data, colWidths=[PW*0.6, PW*0.4])
                brand_t.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#080C16")),
                    ("LEFTPADDING", (0,0), (0,0), 10),
                    ("RIGHTPADDING", (1,0), (1,0), 10),
                    ("TOPPADDING", (0,0), (-1,-1), 12),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 12),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                    # Left green accent line
                    ("LINEBEFORE", (0,0), (0,0), 3, ACCENT),
                ]))
                story.append(brand_t)
                
                # Subtle secondary bar
                badge_p = Paragraph("INSTITUTIONAL GRADE • SECURE REPORT • VERIFIED AI INSIGHTS", sBadge)
                badge_t = Table([[badge_p]], colWidths=[PW])
                badge_t.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#1E3A8A")),
                    ("TOPPADDING", (0,0), (-1,-1), 2),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                    ("BOTTOMBORDER", (0,0), (-1,-1), 1, ACCENT),
                ]))
                story.append(badge_t)
                story.append(Spacer(1, 10*mm))

                for idx, msg in enumerate(history):
                    is_user = msg["role"] == "user"
                    raw = msg["content"]

                    if is_user:
                        lbl_text = "YOU"
                        lbl_color = USER_C
                        bg_color = USER_BG
                        border_color = USER_C
                        # User messages are usually short, but still...
                        body_paras = [Paragraph(clean(raw), sUser)]
                    else:
                        lbl_text = "FINSAARTHI AI"
                        lbl_color = AI_C
                        bg_color = AI_BG
                        border_color = AI_C
                        body_paras = parse_ai(raw)

                    # Header row for the message
                    lbl_para = Paragraph(lbl_text, ParagraphStyle(
                        f"lbl{idx}", fontName=BOLD, fontSize=7,
                        textColor=lbl_color, spaceAfter=2))
                    
                    # Construct table rows: [Strip, Content]
                    # Row 0: Label
                    # Row 1-N: Body paragraphs
                    table_data = [["", lbl_para]]
                    for p in body_paras:
                        table_data.append(["", p])

                    # Create the table
                    # Col 0: 2mm wide strip, Col 1: PW - 2mm content
                    t = Table(table_data, colWidths=[2*mm, PW - 2*mm], splitByRow=1)
                    
                    # Style the table to look like a card
                    t_style = [
                        # Strip background (Col 0)
                        ("BACKGROUND", (0, 0), (0, -1), border_color),
                        # Main background (Col 1)
                        ("BACKGROUND", (1, 0), (1, -1), bg_color),
                        # Alignment and padding
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (1, 0), (1, -1), 10),
                        ("TOPPADDING", (1, 0), (1, 0), 8),      # Label top pad
                        ("BOTTOMPADDING", (1, -1), (1, -1), 8), # Last para bottom pad
                        # Intermediate row padding
                        ("TOPPADDING", (1, 1), (1, -1), 2),
                        ("BOTTOMPADDING", (1, 0), (1, -2), 2),
                    ]
                    t.setStyle(TableStyle(t_style))

                    story.append(t)
                    story.append(Spacer(1, 4*mm))

                doc.build(story)
                return buf.getvalue()

            if st.session_state.chat_history:
                pdf_bytes = generate_chat_pdf(st.session_state.chat_history)
                st.download_button(
                    "⬇️ Export as PDF",
                    data=pdf_bytes,
                    file_name="finsaarthi_conversation.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        with col_info:
            msg_count = len([m for m in st.session_state.chat_history if m["role"] == "user"])
            st.markdown(
                f"<div style='font-size:0.72rem;color:var(--text4);padding-top:0.55rem;'>"
                f"💬 {msg_count} question{'s' if msg_count != 1 else ''} asked · "
                f"Responses are AI-generated, not SEBI-registered advice.</div>",
                unsafe_allow_html=True
            )
