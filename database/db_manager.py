# ============================================================
# database/db_manager.py
# SQLite database manager for watchlists, portfolio, and history
# (Supports user-isolated sessions via browser cookies)
# ============================================================

import sqlite3
import json
import os
import uuid
import datetime
import streamlit as st
import streamlit.components.v1 as components
from config.settings import settings

def get_user_id() -> str:
    """Get or generate a persistent unique ID for the user using cookies."""
    # 1. Use session state if already loaded to avoid reading cookies constantly
    if "fsaarthi_user_id" in st.session_state:
        return st.session_state.fsaarthi_user_id
        
    user_id = None
    
    # 2. Try reading from Streamlit cookies (Streamlit >= 1.40)
    try:
        if hasattr(st, "context") and hasattr(st.context, "cookies"):
            user_id = st.context.cookies.get("fsaarthi_user_id")
    except Exception:
        pass
        
    # 3. If no cookie found, generate a new UUID and inject JS to store it
    if not user_id:
        user_id = str(uuid.uuid4())
        # Inject JavaScript to set a 1-year cookie
        js = f"""
        <script>
            // Set cookie at the root path for 1 year
            document.cookie = "fsaarthi_user_id={user_id}; path=/; max-age=31536000";
        </script>
        """
        components.html(js, height=0, width=0)
        
    # Save in session state for fast access during the rest of the session
    st.session_state.fsaarthi_user_id = user_id
    return user_id

def get_user_db_path() -> str:
    uid = get_user_id()
    # Remove any non-alphanumeric characters just to be safe
    safe_uid = "".join(c for c in uid if c.isalnum() or c == '-')
    # Create a unique database file for this user
    path = os.path.join(os.path.dirname(settings.DB_PATH), f"user_data_{safe_uid}.db")
    return path

def get_connection() -> sqlite3.Connection:
    """Create and return a database connection specific to the user."""
    db_path = get_user_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Create all required tables if they don't exist for the current user."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Watchlist table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                company_name TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)

        # Portfolio table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                company_name TEXT,
                buy_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                buy_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Price alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                target_price REAL NOT NULL,
                alert_type TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Analysis history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                analysis_type TEXT,
                result_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database initialization error: {e}")

# ── Watchlist Operations ──────────────────────────────────────

def add_to_watchlist(symbol: str, company_name: str = "", notes: str = "") -> dict:
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO watchlist (symbol, company_name, notes) VALUES (?, ?, ?)",
            (symbol.upper(), company_name, notes)
        )
        conn.commit()
        return {"success": True, "message": f"{symbol} added to watchlist"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()

def remove_from_watchlist(symbol: str) -> dict:
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper(),))
        conn.commit()
        return {"success": True, "message": f"{symbol} removed from watchlist"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()

def get_watchlist() -> list:
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM watchlist ORDER BY added_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

# ── Portfolio Operations ──────────────────────────────────────

def add_to_portfolio(symbol: str, company_name: str, buy_price: float,
                     quantity: int, buy_date: str, notes: str = "") -> dict:
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO portfolio (symbol, company_name, buy_price, quantity, buy_date, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (symbol.upper(), company_name, buy_price, quantity, buy_date, notes)
        )
        conn.commit()
        return {"success": True, "message": f"Added {quantity} shares of {symbol} at ₹{buy_price}"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()

def get_portfolio() -> list:
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def remove_from_portfolio(holding_id: int) -> dict:
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM portfolio WHERE id = ?", (holding_id,))
        conn.commit()
        return {"success": True, "message": "Holding removed"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        conn.close()

# ── Analysis History ──────────────────────────────────────────

def save_analysis(symbol: str, analysis_type: str, result: dict):
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO analysis_history (symbol, analysis_type, result_json) VALUES (?, ?, ?)",
            (symbol.upper(), analysis_type, json.dumps(result))
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
