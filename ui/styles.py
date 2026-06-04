def get_responsive_css():
    return """
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,300,0,0&display=swap");

/* ── DESIGN TOKENS (ULTRA PREMIUM OBSIDIAN THEME) ── */
:root {
  --bg:        #000000; /* Pure OLED Black */
  --bg2:       #09090B; /* Deep Zinc */
  --bg3:       #18181B; /* Dark Zinc */
  --surface:   rgba(24, 24, 27, 0.45); /* Frosty Zinc */
  --surface2:  rgba(39, 39, 42, 0.65);
  --surface3:  rgba(63, 63, 70, 0.85);
  --border:    rgba(255, 255, 255, 0.08); /* Minimalist thin border */
  --border2:   rgba(255, 255, 255, 0.15); /* Hover border */
  --blue:      #3B82F6; /* Crisp Electric Blue */
  --blue2:     #60A5FA; 
  --blue3:     #1D4ED8; /* Deep Blue for gradients */
  --indigo:    #6366F1;
  --cyan:      #06B6D4;
  --teal:      #14B8A6;
  --green:     #10B981; 
  --green2:    #34D399;
  --lime:      #84CC16;
  --red:       #EF4444; 
  --red2:      #F87171;
  --orange:    #F97316;
  --amber:     #F59E0B;
  --gold:      #FBBF24;
  --purple:    #8B5CF6;
  --pink:      #EC4899;
  --text:      #FFFFFF; /* Pure White */
  --text2:     #E4E4E7; /* Zinc 200 */
  --text3:     #A1A1AA; /* Zinc 400 */
  --text4:     #71717A; /* Zinc 500 */
  --r8:        8px;
  --r12:       12px;
  --r16:       16px;
  --r20:       20px;
}

/* ── BASE ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { background: var(--bg) !important; color: var(--text) !important; font-family: "Inter", sans-serif !important; overflow-x: hidden !important; }
[data-testid="block-container"], .main .block-container, [data-testid="stMainBlockContainer"] { 
    padding-top: 1rem !important; 
    padding-right: 2rem !important; 
    padding-left: 2rem !important; 
    padding-bottom: 2rem !important; 
    font-family: "Inter", sans-serif; 
}
/* Ensure Material Symbols don't get overridden by general rules */
.material-symbols-rounded, .material-icons { font-family: "Material Symbols Rounded" !important; }

.scroll-container {
  display: block !important;
  overflow-x: auto !important;
  overflow-y: hidden !important;
  width: 100% !important;
  -webkit-overflow-scrolling: touch;
  margin: 0 !important;
  padding: 0 !important;
}

    /* Mobile optimization */
    @media (max-width: 768px) {
        html, body, .stApp, [data-testid="block-container"], .main .block-container, [data-testid="stMainBlockContainer"] {
            overflow-x: hidden !important;
            max-width: 100vw !important;
           
        }
        [data-testid="block-container"], .main .block-container, [data-testid="stMainBlockContainer"] { 
            padding-top: 1rem !important; 
            padding-right: 1.25rem !important; 
            padding-left: 1.25rem !important; 
            padding-bottom: 2rem !important;
        }
        /* Force all column blocks to stack vertically on mobile, EXCEPT those marked as .no-stack */
        [data-testid="stHorizontalBlock"]:not(.no-stack) {
            flex-direction: column !important;
            gap: 0.75rem !important;
        }
        [data-testid="stHorizontalBlock"]:not(.no-stack) > div[data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stHorizontalBlock"]:not(.no-stack) > div[data-testid="stColumn"],
        [data-testid="stHorizontalBlock"]:not(.no-stack) > div {
            flex: 0 0 100% !important;
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
        }
        /* Plotly chart full width */
        [data-testid="stPlotlyChart"],
        [data-testid="stPlotlyChart"] > div {
            width: 100% !important;
            min-width: 0 !important;
        }
    }

    /* ── GLOBAL INPUT INSTRUCTIONS HIDE ── */
    [data-testid="InputInstructions"], 
    [data-testid="stTextInput"] small,
    [data-testid="stNumberInput"] small,
    [data-testid="stTextArea"] small { 
      display: none !important; 
      visibility: hidden !important;
      height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
    }

/* ── SUBTLE NOISE TEXTURE OVERLAY ── */
.stApp::after {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 200px 200px;
  opacity: 0.4;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
  background: rgba(10, 10, 10, 0.7) !important;
  backdrop-filter: blur(20px) !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: inset -1px 0 0 rgba(255,255,255,0.02) !important;
}


/* Remove default 16px spacing between sidebar items */
[data-testid="stSidebarHeader"] {
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}

/* NAV radio */
[data-testid="stSidebar"] .stRadio > label { display: none !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 1px !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] { width:100% !important; padding:0 !important; margin:0 !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child { display:none !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:last-child {
  background: transparent !important;
  border-radius: var(--r8) !important;
  padding: 0.5rem 0.8rem !important; /* Increased padding for touch */
  cursor: pointer !important; width: 100% !important;
  transition: all 0.15s ease !important;
  color: var(--text3) !important;
  font-size: 0.85rem !important; font-weight: 500 !important;
  border: 1px solid transparent !important;
  letter-spacing: 0.01em !important;

}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"]:hover > div:last-child {
  background: rgba(255,255,255,0.06) !important;
  color: var(--text) !important; border-color: rgba(255,255,255,0.15) !important;
}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"][aria-checked="true"] > div:last-child {
  background: rgba(255,255,255,0.12) !important;
  color: var(--text) !important; font-weight: 600 !important;
  border-color: rgba(255,255,255,0.3) !important;
  box-shadow: 0 4px 15px rgba(0,0,0,0.5), inset 0 0 0 1px rgba(255,255,255,0.1) !important;
}

/* ── METRIC CARDS ── */
[data-testid="metric-container"] {
  background: var(--surface) !important;
  backdrop-filter: blur(24px) !important; -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid var(--border) !important;
  border-top: 1px solid rgba(255,255,255,0.12) !important;
  border-radius: var(--r16) !important;
  padding: 1.2rem 1.4rem 1.1rem !important;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
  position: relative !important; overflow: hidden !important;
  box-shadow: 0 8px 30px rgba(0,0,0,0.5) !important;
}
[data-testid="metric-container"]::before {
  content: '' !important; position: absolute !important;
  inset: 0 !important; border-radius: var(--r16) !important;
  background: linear-gradient(180deg, rgba(255,255,255,0.04) 0%, transparent 100%) !important;
  pointer-events: none !important;
}
[data-testid="metric-container"]:hover {
  transform: translateY(-3px) !important;
  border-color: var(--border2) !important;
  box-shadow: 0 16px 40px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.05) !important;
  background: var(--surface2) !important;
}
[data-testid="stMetricValue"] {
  font-family: "Outfit", sans-serif !important;
  font-size: clamp(1.2rem, 3vw, 1.55rem) !important; font-weight: 800 !important;
  color: var(--text) !important; letter-spacing: -0.6px !important; line-height: 1.1 !important;
}
[data-testid="stMetricLabel"] {
  font-family: "JetBrains Mono", monospace !important;
  font-size: clamp(0.5rem, 1.5vw, 0.6rem) !important; color: var(--text3) !important;
  text-transform: uppercase !important; letter-spacing: 0.14em !important; font-weight: 500 !important;
  white-space: normal !important; /* Allow wrapping */
}
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; font-weight: 700 !important; }
[data-testid="stMetricDeltaIcon"] { display: none !important; }

/* Responsive Grid Adjustments */
.responsive-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
}

@media (max-width: 768px) {
    .responsive-grid {
        grid-template-columns: 1fr;
    }
}

/* CUSTOM TOP METRICS GRID (Dashboard) */
.dash-metrics-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 2rem;
  width: 100%;
}

@media (max-width: 600px) {
  .dash-metrics-grid {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 0.5rem !important;
  }
  .dash-metric-card {
    min-width: 0 !important;
    max-width: none !important;
    padding: 0.4rem 0.3rem !important;
    min-height: 75px !important;
  }
  .dash-metric-value {
    font-size: 0.9rem !important;
  }
  .dash-metric-label {
    font-size: 0.5rem !important;
  }
}

.dash-metric-card {
  flex: 1 1 200px;
  max-width: 260px;
  min-width: 160px;
  background: var(--surface);
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--border);
  border-top: 1px solid rgba(255,255,255,0.12);
  border-radius: var(--r12);
  padding: 0.5rem 0.4rem;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative; overflow: hidden;
  box-shadow: 0 8px 30px rgba(0,0,0,0.4);
  text-align: center;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 85px;
}
.dash-metric-card:hover {
  transform: translateY(-3px);
  border-color: var(--border2);
  background: var(--surface2);
  box-shadow: 0 16px 40px rgba(0,0,0,0.7);
}
.dash-metric-label {
  font-family: "JetBrains Mono", monospace;
  font-size: 0.58rem; color: var(--text3);
  text-transform: uppercase; letter-spacing: 0.08em; font-weight: 500;
  margin-bottom: 0.2rem;
}
.dash-metric-value {
  font-family: "Outfit", sans-serif;
  font-size: 1.05rem; font-weight: 800;
  color: var(--text); letter-spacing: -0.3px; line-height: 1.1;
  margin-bottom: 0.1rem;
}
.dash-metric-delta {
  font-size: 0.68rem; font-weight: 700;
}
.dash-metric-delta.pos { color: #10B981; }
.dash-metric-delta.neg { color: #EF4444; }
.dash-metric-delta.neu { color: var(--text3); }

/* ── PORTFOLIO METRICS (Premium Large Cards) ── */
.port-metrics-grid {
  display: flex; gap: 1.2rem; width: 100%; margin-bottom: 2rem;
}
.port-metric-card {
  flex: 1; background: #121214;
  border: 1px solid rgba(255,255,255,0.1);
  border-top: 1px solid rgba(255,255,255,0.25);
  border-radius: var(--r16);
  padding: 1.4rem; position: relative; overflow: hidden;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 8px 30px rgba(0,0,0,0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex; flex-direction: column; align-items: flex-start; justify-content: center;
}
.port-metric-card::before {
  content: ''; position: absolute; inset: 0; border-radius: var(--r16);
  background: radial-gradient(600px circle at 0% 0%, rgba(255,255,255,0.08), transparent 40%);
  pointer-events: none;
}
.port-metric-card:hover {
  transform: translateY(-3px); border-color: rgba(255,255,255,0.3);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.1), 0 16px 40px rgba(0,0,0,0.9); 
  background: #18181b;
}
.port-metric-label {
  font-family: "JetBrains Mono", monospace; font-size: 0.65rem; color: var(--text3);
  text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600; margin-bottom: 0.5rem;
  display: flex; align-items: center; gap: 6px;
}
.port-metric-value {
  font-family: "Outfit", sans-serif; font-size: 1.7rem; font-weight: 800;
  color: var(--text); letter-spacing: -0.5px; line-height: 1.1; margin-bottom: 0.3rem;
}
.port-metric-delta {
  font-size: 0.8rem; font-weight: 700; font-family: "JetBrains Mono", monospace;
}
.port-metric-delta.pos { color: #10B981; }
.port-metric-delta.neg { color: #EF4444; }

@media (max-width: 768px) {
  .port-metrics-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem;
  }
  .port-metric-card { padding: 1rem; }
  .port-metric-value { font-size: 1.3rem; }
  .port-metric-label { font-size: 0.55rem; }
}

/* ── FIN-CARD ── */
.fin-card {
  background: var(--surface);
  backdrop-filter: blur(32px); -webkit-backdrop-filter: blur(32px);
  border: 1px solid var(--border);
  border-top: 1px solid rgba(255,255,255,0.12);
  border-radius: var(--r16); padding: clamp(0.8rem, 2vw, 1.2rem) clamp(1rem, 2vw, 1.4rem);
  position: relative; overflow: hidden;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  width: 100%;
  box-shadow: 0 10px 40px rgba(0,0,0,0.4);
}
.fin-card::before {
  content: ''; position: absolute; inset: 0; border-radius: var(--r16);
  background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, transparent 100%);
  pointer-events: none;
}
.fin-card:hover { border-color: var(--border2); box-shadow: 0 16px 50px rgba(0,0,0,0.6); transform: translateY(-3px); }

.fin-card-glow-green { border-color: rgba(16,185,129,0.35) !important; background: linear-gradient(145deg, rgba(16,185,129,0.07), var(--bg3)) !important; }
.fin-card-glow-red   { border-color: rgba(239,68,68,0.35) !important;   background: linear-gradient(145deg, rgba(239,68,68,0.07),   var(--bg3)) !important; }
.fin-card-glow-blue  { border-color: rgba(14,165,233,0.35) !important;  background: linear-gradient(145deg, rgba(14,165,233,0.07),  var(--bg3)) !important; }
.fin-card-glow-amber { border-color: rgba(245,158,11,0.35) !important;  background: linear-gradient(145deg, rgba(245,158,11,0.07),  var(--bg3)) !important; }

/* ── GLASS CARD ── */
.glass-card {
  background: rgba(15,23,41,0.7);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: var(--r16); padding: 1.2rem 1.4rem;
}

/* ── SIGNAL CARDS ── */
.signal-buy  { background: rgba(16,185,129,0.15); backdrop-filter: blur(12px); border:1px solid rgba(16,185,129,0.3);  border-radius:var(--r16); padding:1.2rem; text-align:center; box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
.signal-sell { background: rgba(239,68,68,0.15);  backdrop-filter: blur(12px); border:1px solid rgba(239,68,68,0.3);   border-radius:var(--r16); padding:1.2rem; text-align:center; box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
.signal-hold { background: rgba(245,158,11,0.15); backdrop-filter: blur(12px); border:1px solid rgba(245,158,11,0.3);  border-radius:var(--r16); padding:1.2rem; text-align:center; box-shadow: 0 4px 15px rgba(0,0,0,0.15); }

/* ── TICKER CARD ── */
.ticker-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r12); padding: 0.65rem 1rem; margin: 4px 0;
  display: flex; align-items: center; justify-content: space-between;
  transition: all 0.16s ease; cursor: default;
  position: relative; overflow: hidden;
  flex-wrap: nowrap; /* keep single row always */
  gap: 0.5rem;
  min-width: 0; /* allow shrink */
}
/* Left symbol/name group */
.ticker-card .tc-left {
  display: flex; flex-direction: column;
  flex: 0 0 auto; /* don't grow — let right side anchor to right */
  min-width: 0;
  max-width: 55%; /* cap so price area always visible */
  overflow: hidden;
}
.ticker-card .tc-sym {
  font-family: "JetBrains Mono", monospace;
  font-size: 0.82rem; font-weight: 700; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ticker-card .tc-name {
  font-size: 0.65rem; color: var(--text3);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-top: 1px;
}
/* Right price/signal group */
.ticker-card .tc-right {
  display: flex; align-items: center;
  gap: 0.6rem;
  flex-shrink: 0; /* never shrink */
  margin-left: auto; /* push to far right */
}
.ticker-card .tc-price {
  font-family: "JetBrains Mono", monospace;
  font-size: 0.88rem; font-weight: 700; color: var(--text);
  text-align: right; white-space: nowrap;
}
.ticker-card .tc-chg {
  font-size: 0.7rem; font-weight: 600;
  white-space: nowrap; text-align: right; margin-top: 1px;
}
.ticker-card .tc-chg.pos { color: var(--green); }
.ticker-card .tc-chg.neg { color: var(--red); }
.ticker-card::after {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0;
  width: 3px; border-radius: 3px 0 0 3px;
  background: transparent; transition: background 0.16s;
}
.ticker-card:hover { border-color: var(--border2); background: var(--surface2); transform: translateX(4px); }
.ticker-card.gain::after { background: var(--green); }
.ticker-card.loss::after { background: var(--red); }
.ticker-card.gain:hover { border-color: rgba(16,185,129,0.4); }
.ticker-card.loss:hover { border-color: rgba(239,68,68,0.4); }

/* Mobile tweaks for ticker card */
@media (max-width: 480px) {
  .ticker-card { padding: 0.55rem 0.75rem; }
  .ticker-card .tc-sym { font-size: 0.75rem; }
  .ticker-card .tc-price { font-size: 0.78rem; }
}

/* ── SECTION HEADER ── */
.sec-hdr {
  display: flex; align-items: center; gap: 10px;
  margin: 0.85rem 0 0.65rem;
  flex-wrap: wrap;
}
.sec-hdr-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--blue); flex-shrink: 0;
  box-shadow: 0 0 12px rgba(14,165,233,0.8);
}
.sec-hdr-dot.green { background: var(--green); box-shadow: 0 0 12px rgba(16,185,129,0.8); }
.sec-hdr-dot.red   { background: var(--red);   box-shadow: 0 0 12px rgba(239,68,68,0.8); }
.sec-hdr-dot.amber { background: var(--amber);  box-shadow: 0 0 12px rgba(245,158,11,0.8); }
.sec-hdr-dot.purple{ background: var(--purple); box-shadow: 0 0 12px rgba(168,85,247,0.8); }
.sec-hdr-label {
  font-family: "Inter", sans-serif !important;
  font-size: 0.85rem; font-weight: 700; color: var(--text2);
  text-transform: uppercase; letter-spacing: 0.08em;
  flex: 1;
  min-width: 100px;
}
.sec-hdr::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, var(--border), transparent); max-width: 200px; }

/* ── PAGE HEADER ── */
.pg-header { margin-bottom: 1.6rem; text-align: center; }
.pg-eyebrow {
  font-family: "JetBrains Mono", monospace !important;
  font-size: 0.6rem; color: var(--blue2);
  text-transform: uppercase; letter-spacing: 0.2em;
  margin-bottom: 0.3rem; opacity: 0.9;
  text-align: center;
}
.pg-title {
  font-family: "Inter", sans-serif !important;
  font-size: clamp(1.5rem, 4vw, 2.1rem); font-weight: 800; color: var(--text);
  letter-spacing: -0.8px; line-height: 1.1; margin-bottom: 0.3rem;
  text-shadow: 0 0 20px rgba(255,255,255,0.1);
  text-align: center;
}
.pg-sub { font-size: clamp(0.75rem, 2vw, 0.84rem); color: var(--text3); letter-spacing: 0.01em; text-align: center; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r12) !important;
  padding: 4px !important; gap: 2px !important;
  width: 100% !important; /* Full width on mobile */
  flex-wrap: wrap !important;
}
@media (min-width: 768px) {
  .stTabs [data-baseweb="tab-list"] {
    width: fit-content !important;
    margin: 0 auto !important;
  }
}
.stTabs [data-baseweb="tab"] {
  border-radius: 9px !important; color: var(--text3) !important;
  font-weight: 600 !important; font-size: 0.82rem !important;
  padding: 0.42rem 1.1rem !important; background: transparent !important;
  border: none !important; letter-spacing: 0.01em !important;
  flex: 1 !important; /* Grow on mobile */
  text-align: center !important;
}
.stTabs [aria-selected="true"] {
  background: #FFFFFF !important;
  color: #000000 !important; box-shadow: 0 4px 14px rgba(255,255,255,0.25) !important;
}

/* ── BUTTONS ── */
.stButton > button {
  border-radius: var(--r8) !important;
  font-family: "Outfit", sans-serif !important;
  font-weight: 700 !important; font-size: 0.8rem !important;
  letter-spacing: 0.04em !important;
  transition: all 0.18s cubic-bezier(0.4,0,0.2,1) !important;
  min-height: 44px !important; /* Touch target size */
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--blue3), var(--blue)) !important;
  color: #FFFFFF !important; border: 1px solid rgba(59,130,246,0.5) !important;
  box-shadow: 0 4px 20px rgba(59,130,246,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, var(--blue), var(--blue2)) !important;
  transform: translateY(-2px) !important;
  border-color: rgba(96,165,250,0.8) !important;
  box-shadow: 0 8px 25px rgba(59,130,246,0.5) !important;
}
.stButton > button[kind="secondary"] {
  background: var(--surface2) !important; color: var(--text2) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: var(--border2) !important; color: var(--text) !important; background: var(--surface3) !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea > div > div > textarea,
.stDateInput > div > div > input {
  background: rgba(10, 10, 12, 0.95) !important; 
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: var(--r8) !important; 
  color: #FFFFFF !important;
  font-family: "Space Grotesk", sans-serif !important; 
  font-size: 0.88rem !important;
  transition: all 0.2s ease !important;
  min-height: 44px !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: rgba(255, 255, 255, 0.3) !important;
  background: #000000 !important;
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.05) !important;
}
.stSelectbox > div > div {
  background: rgba(10, 10, 12, 0.95) !important; 
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: var(--r8) !important; 
  color: #FFFFFF !important;
  min-height: 44px !important;
  transition: all 0.2s ease !important;
}
.stSelectbox > div > div:focus-within {
  border-color: rgba(255, 255, 255, 0.3) !important;
  background: #000000 !important;
}
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stTextArea label, .stDateInput label, .stCheckbox label, .stSlider label {
  font-family: "JetBrains Mono", monospace !important;
  font-size: 0.62rem !important; color: var(--text2) !important;
  text-transform: uppercase !important; letter-spacing: 0.12em !important; font-weight: 500 !important;
}

/* ── RADIO ── */
.stRadio > div { gap: 0.5rem !important; }
.stRadio [data-baseweb="radio"] > div:first-child > div {
  background: var(--surface) !important; border-color: var(--border2) !important;
}
.stRadio [data-baseweb="radio"][aria-checked="true"] > div:first-child > div {
  background: var(--blue) !important; border-color: var(--blue) !important;
}

/* ── CHECKBOX ── */
.stCheckbox > label > div[data-testid="stCheckbox"] {
  background: rgba(10, 10, 12, 0.95) !important; 
  border-color: rgba(255, 255, 255, 0.15) !important;
  border-radius: 5px !important;
}

/* ── SLIDER ── */
.stSlider > div > div > div > div { background: var(--blue) !important; }

/* ── EXPANDER ── */
.streamlit-expanderHeader {
  background: var(--surface) !important;
  backdrop-filter: blur(12px) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r12) !important; color: var(--text2) !important;
  font-family: "Inter", sans-serif !important;
  font-weight: 600 !important; font-size: 0.88rem !important;
  padding: 0.7rem 1rem !important;
}
.streamlit-expanderHeader:hover { border-color: rgba(255,255,255,0.2) !important; color: var(--text) !important; background: var(--surface2) !important; }
.streamlit-expanderContent {
  background: rgba(10,10,10,0.5) !important;
  backdrop-filter: blur(16px) !important;
  border: 1px solid var(--border) !important;
  border-top: none !important; border-radius: 0 0 var(--r12) var(--r12) !important; padding: 1rem !important;
}

/* ── DATAFRAME ── */
.stDataFrame { border: 1px solid var(--border) !important; border-radius: var(--r12) !important; overflow: hidden !important; width: 100% !important; }
[data-testid="stDataFrameResizable"] { border-radius: var(--r12) !important; max-width: 100% !important; }

/* ── ALERTS ── */
.stAlert { border-radius: var(--r8) !important; }
.stInfo    { background: rgba(14,165,233,0.1) !important;  border: 1px solid rgba(14,165,233,0.3) !important;  color: var(--blue2) !important; }
.stSuccess { background: rgba(16,185,129,0.1) !important;  border: 1px solid rgba(16,185,129,0.3) !important; }
.stError   { background: rgba(239,68,68,0.1) !important;   border: 1px solid rgba(239,68,68,0.3) !important; }
.stWarning { background: rgba(245,158,11,0.1) !important;  border: 1px solid rgba(245,158,11,0.3) !important; }

/* ── CHAT (NEW PREMIUM) ── */
.finsaarthi-chat-wrap [data-testid="stChatMessageContent"] { display: none !important; }
.chat-msg-wrap { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 1rem; animation: fadeSlide 0.3s ease; width: 100%; }
.chat-msg-wrap > div:not(.chat-avatar) { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: flex-start; }
.chat-msg-wrap.user-wrap { flex-direction: row-reverse; }
.chat-msg-wrap.user-wrap > div:not(.chat-avatar) { align-items: flex-end; }
@keyframes fadeSlide { from { opacity:0; transform: translateY(8px); } to { opacity:1; transform: translateY(0); } }

.chat-avatar {
  width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; font-weight: 700;
}
.chat-avatar.ai-avatar {
  background: linear-gradient(135deg, var(--blue), #6366F1);
  box-shadow: 0 4px 15px rgba(99,102,241,0.35);
  color: white;
}
.chat-avatar.user-avatar {
  background: linear-gradient(135deg, #0F1729, #192540);
  border: 1px solid #253D68; color: var(--blue2);
}

.chat-bubble {
  width: fit-content; min-width: 60px;
  max-width: 100%; padding: 0.85rem 1.1rem;
  border-radius: 16px; font-size: 0.875rem; line-height: 1.5;
  position: relative;
  word-wrap: break-word;
}
.chat-bubble p { margin-bottom: 0.5rem !important; }
.chat-bubble p:last-child { margin-bottom: 0 !important; }
.chat-bubble ul, .chat-bubble ol { margin: 0.4rem 0 !important; padding-left: 1.1rem !important; }
.chat-bubble li { margin-bottom: 0.25rem !important; }
.chat-bubble li:last-child { margin-bottom: 0 !important; }

@media (min-width: 768px) {
    .chat-bubble { max-width: 85%; }
}
.chat-bubble.ai-bubble {
  background: linear-gradient(135deg, rgba(15,23,41,0.95), rgba(20,30,52,0.95));
  border: 1px solid rgba(14,165,233,0.2);
  border-top-left-radius: 4px;
  color: #CBD5E9;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.chat-bubble.user-bubble {
  background: linear-gradient(135deg, rgba(29,78,216,0.4), rgba(99,102,241,0.25));
  border: 1px solid rgba(99,102,241,0.4);
  border-top-right-radius: 4px;
  color: #E2E8F7;
  box-shadow: 0 4px 20px rgba(14,165,233,0.15);
}
.chat-bubble.ai-bubble::before {
  content: ''; position: absolute; top: 10px; left: -8px;
  border: 8px solid transparent;
  border-right-color: rgba(14,165,233,0.2);
  border-left: none;
}
.chat-bubble.user-bubble::before {
  content: ''; position: absolute; top: 10px; right: -8px;
  border: 8px solid transparent;
  border-left-color: rgba(99,102,241,0.4);
  border-right: none;
}
.chat-meta { font-size: 0.68rem; color: var(--text4); margin-top: 4px; }
.user-wrap .chat-meta { text-align: right; }

.chat-input-row {
  margin-top: 0.6rem;
  margin-bottom: 0.4rem;
}
.chat-input-row .stTextInput > div > div > input {
  background: rgba(15,23,41,0.95) !important;
  border: 1px solid rgba(14,165,233,0.25) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(10px);
  color: var(--text) !important;
  font-size: 0.9rem !important;
  padding: 0.7rem 1.1rem !important;
  height: 48px !important;
}
.chat-input-row .stTextInput > div > div > input:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 3px rgba(14,165,233,0.15), 0 8px 30px rgba(0,0,0,0.3) !important;
}
.chat-input-row .stButton > button {
  height: 48px !important;
  border-radius: 14px !important;
  font-size: 1.1rem !important;
  background: linear-gradient(135deg, var(--blue3), var(--blue)) !important;
  border: none !important;
  box-shadow: 0 4px 20px rgba(14,165,233,0.4) !important;
}

/* Suggested questions new style */
.suggest-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.6rem; margin-bottom: 1.2rem; }
.suggest-card {
  background: rgba(15,23,41,0.8); border: 1px solid rgba(28,45,79,0.8);
  border-radius: 12px; padding: 0.7rem 0.9rem;
  cursor: pointer; transition: all 0.2s ease;
  display: flex; align-items: center; gap: 8px;
}
.suggest-card:hover {
  border-color: rgba(14,165,233,0.5);
  background: rgba(14,165,233,0.08);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(14,165,233,0.12);
}
.suggest-icon { font-size: 1.1rem; flex-shrink: 0; }
.suggest-text { font-size: 0.75rem; font-weight: 500; color: var(--text2); line-height: 1.3; }

/* Chat container scroll area */
.chat-scroll-area {
  height: calc(100vh - 360px); min-height: 400px; overflow-y: auto;
  padding: 0.5rem; margin-bottom: 0.5rem;
  border-radius: 16px;
  border: 1px solid rgba(28,45,79,0.6);
  background: rgba(8,12,22,0.6);
  backdrop-filter: blur(8px);
  scrollbar-width: thin; scrollbar-color: var(--border) transparent;
}
.chat-scroll-area::-webkit-scrollbar { width: 4px; }
.chat-scroll-area::-webkit-scrollbar-track { background: transparent; }
.chat-scroll-area::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 10px; }

/* Typing indicator */
.typing-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: var(--blue2); animation: typingBounce 1.2s infinite ease-in-out; margin: 0 2px; }
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }

/* Chat status bar */
.chat-status-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.6rem 1rem; border-radius: 12px;
  background: rgba(15,23,41,0.7); border: 1px solid rgba(28,45,79,0.5);
  margin-bottom: 1rem;
  flex-wrap: wrap; gap: 0.5rem;
}
.chat-status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green);
  box-shadow: 0 0 6px var(--green); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }

/* Welcome state */
.chat-welcome {
  text-align: center; padding: 2.5rem 1rem;
  display: flex; flex-direction: column; align-items: center; gap: 0.8rem;
}
.chat-welcome-icon {
  width: 64px; height: 64px; border-radius: 50%;
  background: linear-gradient(135deg, rgba(14,165,233,0.2), rgba(99,102,241,0.2));
  border: 1px solid rgba(99,102,241,0.3);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.8rem; margin-bottom: 0.5rem;
  box-shadow: 0 8px 30px rgba(99,102,241,0.2);
}
.chat-welcome h3 { font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1.2rem; color: var(--text); margin: 0; }
.chat-welcome p { font-size: 0.82rem; color: var(--text3); margin: 0; max-width: 300px; }

/* Quick questions old style - keep for compat */
.quick-q-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.5rem; margin-bottom: 1rem; }
.quick-q-item {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r8); padding: 0.5rem 0.85rem;
  font-size: 0.76rem; font-weight: 500; color: var(--text2);
  cursor: pointer; transition: all 0.15s;
  text-align: center;
}
.quick-q-item:hover { border-color: var(--blue); color: var(--text); background: rgba(14,165,233,0.1); }

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button {
  background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(20,184,166,0.1)) !important;
  border: 1px solid rgba(16,185,129,0.4) !important;
  color: var(--green2) !important; border-radius: var(--r8) !important;
  font-family: "Outfit", sans-serif !important; font-weight: 700 !important;
  width: 100% !important;
}
@media (min-width: 768px) {
  .stDownloadButton > button { width: auto !important; }
}
.stDownloadButton > button:hover { background: rgba(16,185,129,0.25) !important; transform: translateY(-1px) !important; }

/* ── SPINNER ── */
.stSpinner > div { border-top-color: var(--blue) !important; }

/* ── DIVIDER ── */
hr {
  border: none !important; height: 1px !important;
  background: linear-gradient(90deg, transparent, var(--border) 25%, var(--border2) 50%, var(--border) 75%, transparent) !important;
  margin: 1.1rem 0 !important;
}

/* ── MISC ── */
#MainMenu, footer { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
[data-testid="stAppDeployButton"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
.block-container { position: relative; z-index: 1; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }

/* ── BADGE ── */
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 9px; border-radius: 6px;
  font-family: "JetBrains Mono", monospace !important;
  font-size: 0.68rem; font-weight: 600; letter-spacing: 0.04em;
  white-space: nowrap;
}
.badge-green { background: rgba(16,185,129,0.15); color: var(--green2); border: 1px solid rgba(16,185,129,0.3); }
.badge-red   { background: rgba(239,68,68,0.15);  color: var(--red2);   border: 1px solid rgba(239,68,68,0.3); }
.badge-blue  { background: rgba(14,165,233,0.15); color: var(--blue2);  border: 1px solid rgba(14,165,233,0.3); }
.badge-amber { background: rgba(245,158,11,0.15); color: var(--gold);   border: 1px solid rgba(245,158,11,0.3); }
.badge-live  { background: rgba(16,185,129,0.18); color: var(--green2); border: 1px solid rgba(16,185,129,0.4);
               animation: blink-live 2s ease-in-out infinite; }
@keyframes blink-live { 0%,100% { opacity:1; } 50% { opacity:0.5; } }

/* ── STAT ROW (fundamental kv) ── */
.stat-row { display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid rgba(28,45,79,0.5); flex-wrap: wrap; gap: 0.5rem; }
.stat-row:last-child { border-bottom:none; }
.stat-key { font-size:0.76rem; color:var(--text2); }
.stat-val { font-family:"JetBrains Mono",monospace !important; font-size:0.8rem; font-weight:600; color:var(--text); text-align:right;}

/* ── PROGRESS BAR ── */
.prog-wrap { margin: 0.35rem 0; }
.prog-label { display:flex; justify-content:space-between; font-size:0.74rem; color:var(--text2); margin-bottom:3px; }
.prog-track { background:var(--border); border-radius:4px; height:6px; overflow:hidden; width: 100%; }
.prog-fill  { height:100%; border-radius:4px; transition:width 0.5s ease; }

/* ── NEWS CARD ── */
.news-item {
  background: var(--surface);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-left: 3px solid transparent;
  border-radius: 0 var(--r12) var(--r12) 0;
  padding: 0.9rem 1.1rem; margin: 5px 0;
  transition: all 0.2s ease;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.news-item:hover { border-color: rgba(255,255,255,0.2); background: var(--surface2); transform: translateX(4px); box-shadow: 0 4px 15px rgba(0,0,0,0.15); }
.news-item.pos { border-left-color: var(--green); }
.news-item.neg { border-left-color: var(--red); }
.news-item.neu { border-left-color: var(--text3); }

/* ── RESPONSIVE TABLES ── */
.table-container {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

.holding-hdr, .wl-hdr {
  display: grid; 
  grid-template-columns: 2.2fr 0.8fr 1.5fr 1.5fr 1.5fr 1.2fr 0.3fr;
  gap: 12px;
  padding: 0.5rem 1rem;
  font-family: "JetBrains Mono", monospace !important;
  font-size: 0.58rem; color: var(--text3);
  text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;
  border-bottom: 1px solid var(--border);
  min-width: 800px; /* prevent squishing on desktop */
}
.holding-row, .wl-row {
  display: grid; 
  grid-template-columns: 2.2fr 0.8fr 1.5fr 1.5fr 1.5fr 1.2fr 0.3fr;
  gap: 12px;
  align-items: center; padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(28,45,79,0.4);
  transition: background 0.15s;
  min-width: 800px;
}

/* ── MOBILE: wl-row as stacked cards ── */
@media (max-width: 640px) {
  .wl-hdr { display: none !important; } /* hide header row */
  .wl-row {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: wrap !important;
    min-width: 0 !important;
    width: 100% !important;
    gap: 4px 12px !important;
    padding: 0.7rem 0.9rem !important;
    align-items: center !important;
  }
  /* First cell (symbol/name) takes full left, rest flow naturally */
  .wl-row > *:first-child {
    flex: 1 1 auto !important;
    min-width: 0 !important;
  }
  /* Price & change inline after symbol */
  .wl-row > *:nth-child(3) {
    margin-left: auto !important;
    text-align: right !important;
  }
  /* Hide less important cols on very small screens */
  .wl-row > *:nth-child(4),
  .wl-row > *:nth-child(5) {
    display: none !important;
  }
}
/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

.holding-row:hover, .wl-row:hover { background: rgba(14,165,233,0.04); }
.holding-row:last-child, .wl-row:last-child { border-bottom: none; }

/* ── INDEX PILL (top banner) ── */
.idx-pill {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r12); padding: 0.85rem 1.3rem;
  transition: all 0.2s; cursor: default;
  position: relative; overflow: hidden;
  display: flex; flex-direction: column; justify-content: center;
}
.idx-pill::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--blue), var(--cyan), transparent);
  opacity: 0.7;
}
.idx-pill:hover { border-color: var(--border2); transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.35); }
.idx-pill.green-top::before { background: linear-gradient(90deg, transparent, var(--green), var(--teal), transparent); }
.idx-pill.red-top::before   { background: linear-gradient(90deg, transparent, var(--red), var(--orange), transparent); }

/* ── SIDEBAR OVERRIDES ── */
/* Shift content up */
[data-testid="stSidebarHeader"] {
  padding-top: 0.2rem !important;
  padding-bottom: 0rem !important;
}
[data-testid="stSidebarUserContent"] {
  padding-top: 0rem !important;
  padding-bottom: 0rem !important;
}
/* Radio items styling to mimic the mockup */
.stRadio > div[role="radiogroup"] {
  gap: 0px !important;
}
.stRadio label {
  background: transparent !important;
  border: 1px solid rgba(255,255,255,0.05) !important;
  border-radius: 12px !important;
  margin-bottom: 6px !important;
  padding: 7px 14px !important;
  transition: all 0.2s ease !important;
  display: flex !important;
  align-items: center !important;
  width: 100% !important;
  cursor: pointer !important;
}
.stRadio label:hover {
  background: rgba(255,255,255,0.03) !important;
  border-color: rgba(255,255,255,0.15) !important;
}
/* Selected state */
.stRadio label[data-checked="true"], 
.stRadio div[aria-checked="true"],
.stRadio div[data-baseweb="radio"][aria-checked="true"] label {
  background: rgba(14,165,233,0.15) !important;
  border: 1px solid rgba(14,165,233,0.4) !important;
}
/* Hide the default radio circle completely */
.stRadio label > div:first-child,
.stRadio input[type="radio"] {
  display: none !important;
}
/* Text styling inside label */
.stRadio label > div:not(:first-child),
.stRadio label p {
  font-family: 'Inter', sans-serif !important;
  font-size: 0.95rem !important;
  font-weight: 500 !important;
  padding-left: 0 !important;
  color: #CBD5E1 !important;
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  margin: 0 !important;
}
.stRadio label[data-checked="true"] > div:not(:first-child),
.stRadio div[aria-checked="true"] label > div:not(:first-child),
.stRadio label[data-checked="true"] p,
.stRadio div[aria-checked="true"] p {
  color: var(--blue2) !important;
}
/* White dot for active state */
.stRadio label[data-checked="true"]::after,
.stRadio div[aria-checked="true"] label::after {
  content: "•" !important;
  color: white !important;
  margin-left: auto !important;
  font-size: 1.5rem !important;
  line-height: 0 !important;
}
div[data-baseweb="radio"][aria-checked="true"] label {
  color: var(--blue2) !important;
}
/* White dot for active state */
div[data-baseweb="radio"][aria-checked="true"] label::after {
  content: "•";
  color: white;
  margin-left: auto;
  font-size: 1.5rem;
  line-height: 0;
}

/* Inject Material Icons using CSS */
.stRadio label p::before {
  font-family: 'Material Symbols Rounded' !important;
  margin-right: 12px;
  font-size: 1.25rem;
  font-weight: 300;
  opacity: 0.8;
  vertical-align: middle;
}
.stRadio label:nth-child(1) p::before { content: "speed"; }
.stRadio label:nth-child(2) p::before { content: "candlestick_chart"; }
.stRadio label:nth-child(3) p::before { content: "swap_horiz"; }
.stRadio label:nth-child(4) p::before { content: "psychology"; }
.stRadio label:nth-child(5) p::before { content: "pie_chart"; }
.stRadio label:nth-child(6) p::before { content: "format_list_bulleted"; }
.stRadio label:nth-child(7) p::before { content: "newspaper"; }
.stRadio label:nth-child(8) p::before { content: "calculate"; }
.stRadio label:nth-child(9) p::before { content: "smart_toy"; }

/* AI Chat Gradient Styling */
.stRadio label:nth-child(9) {
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.15), rgba(59, 130, 246, 0.15)) !important;
  border-color: rgba(139, 92, 246, 0.3) !important;
}
.stRadio label:nth-child(9):hover {
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.25), rgba(59, 130, 246, 0.25)) !important;
}
.stRadio label:nth-child(9)[data-checked="true"] {
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.3), rgba(59, 130, 246, 0.4)) !important;
  border-color: rgba(139, 92, 246, 0.5) !important;
}

/* ── FULL SCREEN MODAL (Mobile Chart) ── */
@media (max-width: 768px) {
  [data-testid="stDialog"] {
    width: 100vw !important;
    height: 100vh !important;
    max-width: 100vw !important;
    max-height: 100vh !important;
    margin: 0 !important;
    padding: 0 !important;
    border-radius: 0 !important;
    background: var(--bg) !important;
  }
  [data-testid="stDialog"] > div:first-child {
    padding: 1rem 0.5rem !important;
    height: 100% !important;
    display: flex;
    flex-direction: column;
  }
  [data-testid="stDialog"] > div:first-child > div[data-testid="stVerticalBlock"] {
    flex: 1;
    overflow: hidden;
  }
  /* Remove overlay background to avoid double darkness if preferred, or keep it */
}
  /* ── FORCE HORIZONTAL (FOR PREMIUM ROWS) ── */
  .force-horizontal [data-testid="stHorizontalBlock"] {
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 0.5rem !important;
  }
  .force-horizontal [data-testid="stColumn"] {
    flex: 1 1 auto !important;
    width: auto !important;
    min-width: 0 !important;
  }
  @media (max-width: 768px) {
    .force-horizontal .cyber-badge {
        padding: 2px 6px !important;
        font-size: 0.6rem !important;
    }
    .force-horizontal .cyber-sym { font-size: 0.95rem !important; }
    .force-horizontal .cyber-px { font-size: 0.9rem !important; }
    .force-horizontal .cyber-name { display: none; } /* Hide name on mobile for more space */
  }
</style>
"""
