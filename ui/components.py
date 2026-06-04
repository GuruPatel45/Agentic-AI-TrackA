import streamlit as st

def page_header(eyebrow, title, sub):
    st.markdown(f"""
    <div class="pg-header">
      <div class="pg-eyebrow">⬡ &nbsp;{eyebrow}</div>
      <div class="pg-title">{title}</div>
      <div class="pg-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def sec_hdr(label, dot_color="blue"):
    st.markdown(f"""
    <div class="sec-hdr">
      <div class="sec-hdr-dot {dot_color}"></div>
      <div class="sec-hdr-label">{label}</div>
    </div>""", unsafe_allow_html=True)

def ticker_card(symbol: str, name: str, price: float, change_pct: float, signal: str = ""):
    gain_class = "gain" if change_pct >= 0 else "loss"
    arrow = "▲" if change_pct >= 0 else "▼"
    chg_class = "pos" if change_pct >= 0 else "neg"
    price_fmt = f"₹{price:,.2f}" if price else "—"
    chg_fmt   = f"{arrow} {abs(change_pct):.2f}%"

    signal_html = ""
    if signal:
        sig_colors = {
            "BUY":  ("rgba(16,185,129,0.15)", "#10B981", "rgba(16,185,129,0.4)"),
            "SELL": ("rgba(239,68,68,0.15)",  "#EF4444", "rgba(239,68,68,0.4)"),
            "HOLD": ("rgba(245,158,11,0.15)", "#F59E0B", "rgba(245,158,11,0.4)"),
        }
        bg, fg, br = sig_colors.get(signal.upper(), ("rgba(100,116,139,0.15)", "#94A3B8", "rgba(100,116,139,0.3)"))
        signal_html = f"""
        <span style="
          background:{bg}; color:{fg}; border:1px solid {br};
          border-radius:6px; padding:2px 8px;
          font-family:'JetBrains Mono',monospace;
          font-size:0.6rem; font-weight:700;
          letter-spacing:0.05em; white-space:nowrap;
          flex-shrink:0;
        ">{signal.upper()}</span>"""

    html = f"""
    <div class="ticker-card {gain_class}">
      <div class="tc-left">
        <span class="tc-sym">{symbol}</span>
        <span class="tc-name">{name}</span>
      </div>
      <div class="tc-right">
        <div style="text-align:right;">
          <div class="tc-price">{price_fmt}</div>
          <div class="tc-chg {chg_class}">{chg_fmt}</div>
        </div>
        {signal_html}
      </div>
    </div>"""
    
    st.markdown(html, unsafe_allow_html=True)

def prog_bar(label, value_str, pct, color="#3B82F6"):
    st.markdown(f"""
    <div class="prog-wrap">
      <div class="prog-label"><span>{label}</span><span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;">{value_str}</span></div>
      <div class="prog-track"><div class="prog-fill" style="width:{min(pct,100)}%;background:{color};"></div></div>
    </div>""", unsafe_allow_html=True)

def stat_row(key, val, val_color=None):
    col_style = f"color:{val_color};" if val_color else ""
    st.markdown(f"""
    <div class="stat-row">
      <span class="stat-key">{key}</span>
      <span class="stat-val" style="{col_style}">{val}</span>
    </div>""", unsafe_allow_html=True)

def get_metric_html(label, value, delta_text="", delta_type="neu"):
    arrow = "▲ " if delta_type == "pos" else ("▼ " if delta_type == "neg" else "")
    if delta_type == "neu" and delta_text and not delta_text.startswith(("—", "N/A", "Refresh", "Add")): 
        arrow = "• "
    return f'<div class="dash-metric-card"><div class="dash-metric-label">{label}</div><div class="dash-metric-value">{value}</div><div class="dash-metric-delta {delta_type}">{arrow}{delta_text.replace("+","").replace("-","")}</div></div>'

def render_metrics_grid(metrics_list):
    html = '<div class="dash-metrics-grid">'
    for m in metrics_list:
        html += get_metric_html(m.get("label", ""), m.get("value", ""), m.get("delta_text", ""), m.get("delta_type", "neu"))
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
