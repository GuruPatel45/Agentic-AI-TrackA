# ============================================================
# database/db_manager.py
# In-memory session state manager for watchlists, portfolio, and history
# ============================================================

import json
from datetime import datetime
import streamlit as st

def initialize_database():
    """Initialize session state variables if they don't exist."""
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []
    if "next_watchlist_id" not in st.session_state:
        st.session_state.next_watchlist_id = 1
    if "next_portfolio_id" not in st.session_state:
        st.session_state.next_portfolio_id = 1

# ── Watchlist Operations ──────────────────────────────────────

def add_to_watchlist(symbol: str, company_name: str = "", notes: str = "") -> dict:
    """Add a stock to the watchlist in session state."""
    initialize_database()
    symbol = symbol.upper()
    # Check if already exists
    for item in st.session_state.watchlist:
        if item["symbol"] == symbol:
            item["company_name"] = company_name
            item["notes"] = notes
            return {"success": True, "message": f"{symbol} updated in watchlist"}
            
    item = {
        "id": st.session_state.next_watchlist_id,
        "symbol": symbol,
        "company_name": company_name,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "notes": notes
    }
    st.session_state.next_watchlist_id += 1
    st.session_state.watchlist.append(item)
    return {"success": True, "message": f"{symbol} added to watchlist"}

def remove_from_watchlist(symbol: str) -> dict:
    """Remove a stock from the watchlist in session state."""
    initialize_database()
    symbol = symbol.upper()
    original_len = len(st.session_state.watchlist)
    st.session_state.watchlist = [item for item in st.session_state.watchlist if item["symbol"] != symbol]
    
    if len(st.session_state.watchlist) < original_len:
        return {"success": True, "message": f"{symbol} removed from watchlist"}
    return {"success": False, "message": f"{symbol} not found in watchlist"}

def get_watchlist() -> list:
    """Get all stocks in the watchlist."""
    initialize_database()
    # Return reverse order to simulate ORDER BY added_at DESC
    return list(reversed(st.session_state.watchlist))

# ── Portfolio Operations ──────────────────────────────────────

def add_to_portfolio(symbol: str, company_name: str, buy_price: float,
                     quantity: int, buy_date: str, notes: str = "") -> dict:
    """Add a stock holding to the portfolio in session state."""
    initialize_database()
    item = {
        "id": st.session_state.next_portfolio_id,
        "symbol": symbol.upper(),
        "company_name": company_name,
        "buy_price": buy_price,
        "quantity": quantity,
        "buy_date": buy_date,
        "notes": notes,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.next_portfolio_id += 1
    st.session_state.portfolio.append(item)
    return {"success": True, "message": f"Added {quantity} shares of {symbol} at ₹{buy_price}"}

def get_portfolio() -> list:
    """Get all portfolio holdings."""
    initialize_database()
    return list(reversed(st.session_state.portfolio))

def remove_from_portfolio(holding_id: int) -> dict:
    """Remove a portfolio holding by ID."""
    initialize_database()
    original_len = len(st.session_state.portfolio)
    st.session_state.portfolio = [item for item in st.session_state.portfolio if item["id"] != holding_id]
    
    if len(st.session_state.portfolio) < original_len:
        return {"success": True, "message": "Holding removed"}
    return {"success": False, "message": "Holding not found"}

# ── Analysis History ──────────────────────────────────────────

def save_analysis(symbol: str, analysis_type: str, result: dict):
    """Save an analysis result to history."""
    initialize_database()
    item = {
        "symbol": symbol.upper(),
        "analysis_type": analysis_type,
        "result_json": json.dumps(result),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.analysis_history.append(item)
