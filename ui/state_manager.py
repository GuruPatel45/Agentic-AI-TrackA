import streamlit as st

def initialize_session_state():
    """Robust initialization of all Streamlit session state variables."""
    defaults = {
        "agent": None,
        "chat_history": [],
        "agent_error": None,
        "selected_symbol": "",
        "nav_page": "Dashboard",
        "auto_analyze": None,
        "compare_symbols": "TCS.NS, INFY.NS, WIPRO.NS",
        "market_mood_cache": None,
        "portfolio_cache": None,
        "watchlist_cache": None,
        "_chat_draft": "",
        "prefill_q": "",
        "last_refresh_time": 0
    }
    
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
            
    # Process query params safely without breaking state
    try:
        if hasattr(st, "query_params"):
            if "symbol" in st.query_params:
                st.session_state["selected_symbol"] = st.query_params["symbol"]
            if "page" in st.query_params:
                st.session_state["nav_page"] = st.query_params["page"]
                st.query_params.clear()
    except Exception as e:
        pass # Ignore errors clearing query params in older Streamlit versions
