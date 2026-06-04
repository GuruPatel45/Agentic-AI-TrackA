import streamlit as st
from tools.stock_tools import get_stock_price
from tools.ai_signals import get_market_mood, get_top_movers, get_sector_heatmap, get_52week_pulse
from database.db_manager import get_portfolio, get_watchlist
from ui.components import page_header, sec_hdr, ticker_card, prog_bar
from ui.charts import create_market_mood_chart
from app import render_interactive_chart  # Import from app or move chart functions later

def show():
    page_header("Live Overview", "Market Dashboard", "Real-time pulse of Indian equity markets")

    # ── Load dashboard data sequentially to ensure stability ──
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

    # ── Top 5 index / portfolio metrics ──────────────────────
    metrics = []
    
    # Nifty 50
    if "error" not in nifty:
        nifty_dt = "pos" if nifty["change_pct"] >= 0 else "neg"
        metrics.append({
            "label": "🔵 Nifty 50",
            "value": f"{nifty['current_price']:,.2f}",
            "delta_text": f"{nifty['change_pct']:+.2f}%",
            "delta_type": nifty_dt
        })
    else:
        st.error(f"DEBUG NIFTY: {nifty}")
        metrics.append({"label": "🔵 Nifty 50", "value": "N/A", "delta_text": "—", "delta_type": "neu"})

    # Sensex
    if "error" not in sensex:
        sensex_dt = "pos" if sensex["change_pct"] >= 0 else "neg"
        metrics.append({
            "label": "🟠 Sensex",
            "value": f"{sensex['current_price']:,.2f}",
            "delta_text": f"{sensex['change_pct']:+.2f}%",
            "delta_type": sensex_dt
        })
    else:
        metrics.append({"label": "🟠 Sensex", "value": "N/A", "delta_text": "—", "delta_type": "neu"})

    # Market Mood
    metrics.append({
        "label": "🌡️ Mood",
        "value": mood_data["mood_label"].split(" ")[0],
        "delta_text": f"{mood_data['mood_score']}% score",
        "delta_type": "neu"
    })

    # Portfolio
    if portfolio:
        try:
            portf_syms = [h["symbol"] for h in portfolio]
            from tools.stock_tools import batch_fetch_prices as _bfp
            portf_prices = _bfp(portf_syms)
            total_val = sum(portf_prices.get(h["symbol"], {}).get("current_price", h["buy_price"]) * h["quantity"] for h in portfolio)
            total_inv = sum(h["buy_price"] * h["quantity"] for h in portfolio)
            pnl = total_val - total_inv
            pnl_pct = (pnl / total_inv * 100) if total_inv > 0 else 0
            metrics.append({
                "label": "💼 Portfolio",
                "value": f"₹{total_val:,.0f}",
                "delta_text": f"{pnl_pct:+.1f}%",
                "delta_type": "pos" if pnl >= 0 else "neg"
            })
        except:
            metrics.append({"label": "💼 Portfolio", "value": "—", "delta_text": "Refresh", "delta_type": "neu"})
    else:
        metrics.append({"label": "💼 Portfolio", "value": "—", "delta_text": "Empty", "delta_type": "neu"})

    # Watchlist
    metrics.append({
        "label": "📋 Watchlist",
        "value": str(len(wl_items)),
        "delta_text": f"{len(portfolio)} holds",
        "delta_type": "neu"
    })

    from ui.components import render_metrics_grid
    render_metrics_grid(metrics)

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

        # Mood chart (Plotly)
        fig_mood = create_market_mood_chart(score)
        st.plotly_chart(fig_mood, use_container_width=True)

        st.markdown(f"""
        <div class="fin-card" style="text-align:center;padding:1.2rem 1rem; margin-top:0.5rem; background: var(--surface); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: var(--r16); box-shadow: 0 4px 20px rgba(0,0,0,0.2);">
          <div style="font-family:'Inter',sans-serif;font-size:1.6rem;font-weight:800;color:{mc}; text-shadow: 0 0 15px {mc}66;">
            {mood_data["mood_label"]}
          </div>
          <div style="display:flex;justify-content:center;gap:1rem;margin-top:0.8rem;">
            <div style="text-align:center;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;color:#10B981;">{bull}%</div>
              <div style="font-size:0.65rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em; margin-top: 2px;">Bull</div>
            </div>
            <div style="width:1px;background:var(--border2);"></div>
            <div style="text-align:center;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;color:var(--text2);">{neu}%</div>
              <div style="font-size:0.65rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em; margin-top: 2px;">Neu</div>
            </div>
            <div style="width:1px;background:var(--border2);"></div>
            <div style="text-align:center;">
              <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:700;color:#EF4444;">{bear}%</div>
              <div style="font-size:0.65rem;color:var(--text3);text-transform:uppercase;letter-spacing:0.1em; margin-top: 2px;">Bear</div>
            </div>
          </div>
          <div style="font-size:0.75rem;color:var(--text3);margin-top:0.8rem;">
            <span style="color:#10B981;">↑ {mood_data.get("gainers",0)} Advancing</span> &nbsp;·&nbsp; <span style="color:#EF4444;">↓ {mood_data.get("losers",0)} Declining</span>
          </div>
        </div>""", unsafe_allow_html=True)

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
            with st.container(height=390, border=False):
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
