# ============================================================
# tools/stock_tools.py
# Financial data tools using yfinance — stock prices, indicators
# ============================================================

import logging
import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from cachetools import TTLCache
from typing import Optional, List
from config.settings import settings

logger = logging.getLogger(__name__)

# Create a robust session to bypass cloud blocking
_session = requests.Session()
_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
})

try:
    import os
    yf.set_tz_cache_location(os.path.join(os.getcwd(), ".yf_cache"))
except Exception:
    pass

_cache = TTLCache(maxsize=200, ttl=settings.CACHE_TTL_SECONDS)


def _get_st_cache_data():
    try:
        import streamlit as st
        def st_cache_wrapper(**kwargs):
            kwargs["show_spinner"] = False
            return st.cache_data(**kwargs)
        return st_cache_wrapper
    except ImportError:
        def _noop(**kwargs):
            def decorator(fn):
                return fn
            return decorator
        return _noop


# -------------------------------------------------------------
# Helper: Retry wrapper for yfinance
# -------------------------------------------------------------
def fetch_with_retry(symbol, retries=2):
    """Fast retry — no sleep, yfinance batch where possible."""
    periods = ["5d", "1mo"]
    for i in range(retries):
        for period in periods:
            try:
                ticker = yf.Ticker(symbol, session=_session)
                hist = ticker.history(period=period)
                if not hist.empty:
                    return ticker, hist
            except Exception:
                pass
    return None, pd.DataFrame()


def batch_fetch_prices(symbols: List[str]) -> dict:
    """
    High-performance, robust price fetching for multiple symbols.
    Uses parallel execution to ensure speed and accuracy.
    """
    results = {}
    to_fetch = [s for s in symbols if f"price_{s}" not in _cache]
    
    # Add cached items first
    for s in symbols:
        if f"price_{s}" in _cache:
            results[s] = _cache[f"price_{s}"]

    if not to_fetch:
        return results

    def _fetch_single(sym):
        try:
            ticker = yf.Ticker(sym, session=_session)
            # Fetch 5 days to ensure we have at least 2 points for change calculation
            hist = ticker.history(period="5d", interval="1d")
            
            if hist.empty:
                # Fallback to fast_info for current price
                px = ticker.fast_info.get("last_price")
                if px:
                    return sym, {
                        "symbol": sym,
                        "current_price": round(px, 2),
                        "change_pct": 0,
                        "company_name": sym
                    }
                return sym, {"error": "No data"}

            # Reliable column access
            cp = float(hist["Close"].iloc[-1])
            pp = float(hist["Close"].iloc[-2]) if len(hist) > 1 else cp
            change_pct = ((cp - pp) / pp * 100) if pp else 0
            
            return sym, {
                "symbol": sym,
                "current_price": round(cp, 2),
                "change_pct": round(change_pct, 2),
                "company_name": sym 
            }
        except Exception as e:
            return sym, {"error": str(e)}

    # Parallel Fetch using ThreadPoolExecutor for I/O bound yfinance calls
    with ThreadPoolExecutor(max_workers=min(len(to_fetch), 10)) as executor:
        futures = {executor.submit(_fetch_single, s): s for s in to_fetch}
        for future in as_completed(futures):
            sym, data = future.result()
            if "error" not in data:
                _cache[f"price_{sym}"] = data
            results[sym] = data

    return results


# -------------------------------------------------------------
# CORE DATA FUNCTIONS
# -------------------------------------------------------------
@_get_st_cache_data()(ttl=60)
def get_stock_price(symbol: str, target_date: str = None) -> dict:
    """Get real-time stock price or precise historical data."""
    key = f"price_{symbol}_{target_date if target_date else 'live'}"
    if key in _cache:
        return _cache[key]

    try:
        # --- PRO LEVEL: NSE Official Data Integration ---
        if target_date and symbol.endswith(".NS"):
            try:
                from nsepython import equity_history
                nse_symbol = symbol.split(".")[0]
                # target_date is already DD-MM-YYYY
                df = equity_history(nse_symbol, "EQ", target_date, target_date)
                if not df.empty:
                    price = float(df['CH_CLOSING_PRICE'].iloc[0])
                    open_price = float(df['CH_OPENING_PRICE'].iloc[0]) if 'CH_OPENING_PRICE' in df.columns else price
                    return {
                        "symbol": symbol,
                        "company_name": nse_symbol,
                        "current_price": price,
                        "open_price": open_price,
                        "change": price - float(df['CH_PREVIOUS_CLS_PRC'].iloc[0]),
                        "change_pct": ((price / float(df['CH_PREVIOUS_CLS_PRC'].iloc[0])) - 1) * 100,
                        "previous_close": float(df['CH_PREVIOUS_CLS_PRC'].iloc[0]),
                        "day_high": float(df['CH_TRADE_HIGH_PRICE'].iloc[0]),
                        "day_low": float(df['CH_TRADE_LOW_PRICE'].iloc[0]),
                        "volume": int(df['CH_TOT_TRADED_QTY'].iloc[0]),
                        "source": "NSE India Official"
                    }
            except:
                pass # Fallback to YFinance if NSE site is down

        ticker = yf.Ticker(symbol)
        if target_date:
            # Fallback YFinance Logic for non-NSE stocks or if nsepython fails
            try:
                dt_obj = datetime.strptime(target_date, "%d-%m-%Y")
                start_dt = (dt_obj - timedelta(days=7)).strftime("%Y-%m-%d")
                end_dt = (dt_obj + timedelta(days=2)).strftime("%Y-%m-%d")
                hist = ticker.history(start=start_dt, end=end_dt, auto_adjust=False)
                
                if not hist.empty:
                    target_ts = pd.Timestamp(dt_obj).tz_localize(hist.index.tz)
                    available_dates = hist.index[hist.index <= target_ts]
                    if not available_dates.empty:
                        hist_row = hist.loc[[available_dates[-1]]]
                        actual_price = float(hist_row["Close"].iloc[0])
                        actual_open_price = float(hist_row["Open"].iloc[0]) if "Open" in hist_row.columns else actual_price
                        
                        try:
                            info = ticker.info
                            company_name = info.get("longName") or info.get("shortName") or symbol
                            sector = info.get("sector") or info.get("industry") or "N/A"
                        except:
                            company_name = symbol
                            sector = "N/A"
                            
                        res_dict = {
                            "HISTORICAL_DATA": f"{target_date} (Open: {actual_open_price:.1f}, Close: {actual_price:.1f})",
                            "LIVE_PRICE_TODAY": actual_price,
                            "PREVIOUS_CLOSE_TODAY": actual_price,
                            "current_price": actual_price,
                            "open_price": actual_open_price,
                            "previous_close": actual_price,
                            "symbol": symbol,
                            "company_name": company_name,
                            "change": 0.0,
                            "change_pct": 0.0,
                            "52_week_high": "N/A",
                            "52_week_low": "N/A",
                            "market_cap_str": "N/A",
                            "sector": sector,
                            "last_closing_date": target_date,
                            "search_context": f"Sector: {sector}"
                        }
                        _cache[key] = res_dict
                        return res_dict
                return {"error": "DATA_NOT_FOUND_ON_EXCHANGE"}
            except Exception as e:
                return {"error": f"EXCHANGE_DATA_UNAVAILABLE: {e}"}
        else:
            # For live requests, try to fetch Nifty from nsepython FIRST because yfinance fails often on Streamlit Cloud.
            if symbol == "^NSEI":
                try:
                    # 1. Try nsepython first (Works locally)
                    from nsepython import nse_get_index_quote
                    idx_data = nse_get_index_quote("NIFTY 50")
                    if isinstance(idx_data, dict) and "last" in idx_data:
                        actual_price = float(str(idx_data["last"]).replace(",", ""))
                        prev_close = float(str(idx_data["previousClose"]).replace(",", ""))
                        change = actual_price - prev_close
                        change_pct = (change / prev_close * 100) if prev_close else 0
                        res_dict = {
                            "current_price": actual_price,
                            "open_price": float(str(idx_data.get("open", actual_price)).replace(",", "")),
                            "previous_close": prev_close,
                            "change": change,
                            "change_pct": change_pct,
                            "symbol": symbol,
                            "company_name": "Nifty 50",
                            "52_week_high": float(str(idx_data.get("yearHigh", 0)).replace(",", "")) or "N/A",
                            "52_week_low": float(str(idx_data.get("yearLow", 0)).replace(",", "")) or "N/A",
                            "market_cap_str": "N/A",
                            "sector": "Index",
                            "last_closing_date": "Live",
                            "search_context": "Index: Nifty 50"
                        }
                        _cache[key] = res_dict
                        return res_dict
                except Exception as e:
                    logger.warning(f"nsepython fetch failed: {e}")

                try:
                    # 2. Try Google Finance Scraper (Works on Streamlit Cloud)
                    import urllib.request, re, ssl
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    req = urllib.request.Request('https://www.google.com/finance/quote/NIFTY_50:INDEXNSE', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                    html = urllib.request.urlopen(req, timeout=5, context=ctx).read().decode('utf-8')
                    match = re.search(r'class="YMlKec fxKbKc"[^>]*>([^<]+)<', html)
                    if match:
                        actual_price = float(match.group(1).replace(",", "").replace("₹", ""))
                        # Calculate previous close based on change pct if possible, or just default to 0 change
                        res_dict = {
                            "current_price": actual_price,
                            "open_price": actual_price,
                            "previous_close": actual_price,
                            "change": 0.0,
                            "change_pct": 0.0,
                            "symbol": symbol,
                            "company_name": "Nifty 50",
                            "52_week_high": "N/A",
                            "52_week_low": "N/A",
                            "market_cap_str": "N/A",
                            "sector": "Index",
                            "last_closing_date": "Live",
                            "search_context": "Index: Nifty 50"
                        }
                        _cache[key] = res_dict
                        return res_dict
                except Exception as e:
                    logger.warning(f"Google Finance fetch failed: {e}")

            # Fallback to yfinance if nsepython fails or if it's not an index
            try:
                hist = ticker.history(period="3mo")
            except Exception as e:
                import pandas as pd
                logger.warning(f"yfinance history failed for {symbol}: {e}")
                hist = pd.DataFrame()
        
        # --- PRIMARY DATA FETCH (FAST) ---
        current_price = prev_price = day_high = day_low = open_price = None
        market_cap = week_high = week_low = sector = company_name = "N/A"
        div_yield = 0

        try:
            fast = ticker.fast_info
            current_price = getattr(fast, "last_price", None)
            open_price = getattr(fast, "open", None)
            prev_price = getattr(fast, "previous_close", None)
            day_high = getattr(fast, "day_high", None)
            day_low = getattr(fast, "day_low", None)
            market_cap = getattr(fast, "market_cap", "N/A")
            week_high = getattr(fast, "year_high", None) or getattr(fast, "fifty_two_week_high", None)
            week_low  = getattr(fast, "year_low", None) or getattr(fast, "fifty_two_week_low", None)
        except: pass

        # --- FALLBACKS (HISTORY & INFO) ---
        if current_price is None and not hist.empty:
            current_price = float(hist["Close"].iloc[-1])
            prev_price = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
            
        if open_price is None and not hist.empty:
            open_price = float(hist["Open"].iloc[-1]) if "Open" in hist.columns else current_price
        
        try:
            info = ticker.info
            company_name = info.get("longName") or info.get("shortName") or symbol
            sector = info.get("sector") or info.get("industry") or "N/A"
            div_yield = info.get("dividendYield") or info.get("trailingAnnualDividendYield") or 0
            if not div_yield:
                try:
                    one_year_ago = datetime.now() - timedelta(days=365)
                    divs = ticker.dividends
                    if not divs.empty:
                        div_yield = divs[divs.index >= one_year_ago.strftime('%Y-%m-%d')].sum() / current_price if current_price else 0
                except: pass
            week_high = week_high or info.get("fiftyTwoWeekHigh")
            week_low = week_low or info.get("fiftyTwoWeekLow")
        except: company_name = symbol

        # --- CALCULATION FALLBACK FOR 52W ---
        if week_high is None or week_high == "N/A":
            try:
                h1y = ticker.history(period="1y")
                week_high = float(h1y["High"].max()) if not h1y.empty else "N/A"
                week_low = float(h1y["Low"].min()) if not h1y.empty else "N/A"
            except: pass
        
        # Final Formatting
        mc_final = f"₹{market_cap/10**7:,.0f} Cr" if isinstance(market_cap, (int, float)) else "N/A"
        current_price = current_price or 0
        prev_price = prev_price or current_price
        change = current_price - prev_price
        change_pct = (change / prev_price * 100) if prev_price else 0
        
        if not hist.empty and "Open" not in hist.columns:
            if "Close" in hist.columns:
                hist["Open"] = hist["Close"]
        
        if not hist.empty:
            hist_data_str = ",".join([f"{d.strftime('%d-%m-%Y')} (Open: {o:.1f}, Close: {c:.1f})" for d, o, c in zip(hist.index, hist.get('Open', []), hist.get('Close', []))])
        else:
            hist_data_str = "N/A"
        
        result = {
            "HISTORICAL_DATA": hist_data_str,
            "LIVE_PRICE_TODAY": current_price,
            "PREVIOUS_CLOSE_TODAY": prev_price,
            "current_price": current_price, # Alias for app.py
            "open_price": open_price,
            "previous_close": prev_price,   # Alias for app.py
            "symbol": symbol,
            "company_name": company_name,
            "change": change,
            "change_pct": change_pct,
            "52_week_high": week_high,
            "52_week_low": week_low,
            "market_cap_str": mc_final,
            "sector": sector,
            "last_closing_date": (hist.index[-1].strftime('%d-%m-%Y') if not hist.empty else "N/A"),
            "search_context": f"Sector: {sector}, Market Cap: {mc_final}"
        }
        
        _cache[key] = result
        return result
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"get_stock_price({symbol}) failed: {e}\n{tb}")
        return {"symbol": symbol, "error": tb}




# -------------------------------------------------------------
# HISTORICAL DATA
# -------------------------------------------------------------
@_get_st_cache_data()(ttl=300)
def get_historical_data(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:

    key = f"hist_{symbol}_{period}_{interval}"
    if key in _cache:
        return _cache[key]

    try:

        ticker = yf.Ticker(symbol, session=_session)

        df = ticker.history(period=period, interval=interval)

        if df.empty:
            return pd.DataFrame()

        df.index = pd.to_datetime(df.index)

        df = df[["Open", "High", "Low", "Close", "Volume"]]

        df = df.round(2)

        _cache[key] = df

        return df

    except Exception as e:

        logger.error("get_historical_data failed %s", e)

        return pd.DataFrame()


# -------------------------------------------------------------
# TECHNICAL INDICATORS
# -------------------------------------------------------------
def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df

    close = df["Close"]

    df["SMA_20"] = close.rolling(20).mean()
    df["SMA_50"] = close.rolling(50).mean()

    df["EMA_20"] = close.ewm(span=20, adjust=False).mean()

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()

    df["BB_Upper"] = sma20 + 2 * std20
    df["BB_Lower"] = sma20 - 2 * std20

    return df.round(2)


# -------------------------------------------------------------
# FUNDAMENTAL ANALYSIS
# -------------------------------------------------------------
@_get_st_cache_data()(ttl=600)
def get_fundamental_analysis(symbol: str) -> dict:

    key = f"fundamental_{symbol}"

    if key in _cache:
        return _cache[key]

    try:

        ticker = yf.Ticker(symbol, session=_session)

        # ticker.info has full fundamental data (fast_info is too limited)
        try:
            info = ticker.info
        except Exception:
            info = {}

        def safe_val(key_name, default="N/A"):
            """Safely get a value from info dict, return default if None/missing."""
            val = info.get(key_name, default)
            if val is None or val == "" or val == 0 and key_name not in ("beta",):
                return default
            return val

        def fmt_pct(val):
            """Convert decimal to percentage float, e.g. 0.15 -> 0.15 (kept as float for UI formatting)."""
            if isinstance(val, (int, float)):
                return round(float(val), 4)
            return "N/A"

        def fmt_round(val, decimals=2):
            if isinstance(val, (int, float)):
                return round(float(val), decimals)
            return "N/A"

        # Market cap in Crores (INR)
        market_cap_raw = info.get("marketCap", None)
        market_cap_cr = "N/A"
        if market_cap_raw and isinstance(market_cap_raw, (int, float)) and market_cap_raw > 0:
            market_cap_cr = f"₹{market_cap_raw / 1e7:,.0f} Cr"

        # P/E Ratio - try trailingPE first, then forwardPE
        pe = info.get("trailingPE") or info.get("forwardPE")
        pe_ratio = fmt_round(pe) if pe else "N/A"

        # P/B Ratio
        pb = info.get("priceToBook")
        pb_ratio = fmt_round(pb) if pb else "N/A"

        # EPS (Trailing twelve months)
        eps_raw = info.get("trailingEps") or info.get("forwardEps")
        eps = fmt_round(eps_raw) if eps_raw else "N/A"

        # ROE and ROA (yfinance gives these as decimals e.g. 0.15 = 15%)
        roe_raw = info.get("returnOnEquity")
        roa_raw = info.get("returnOnAssets")
        roe = fmt_pct(roe_raw) if roe_raw is not None else "N/A"
        roa = fmt_pct(roa_raw) if roa_raw is not None else "N/A"

        # Debt to Equity
        de_raw = info.get("debtToEquity")
        debt_to_equity = fmt_round(de_raw) if de_raw is not None else "N/A"

        # Dividend Yield
        div_raw = info.get("dividendYield")
        div_yield = fmt_pct(div_raw) if div_raw is not None else "N/A"

        # Beta
        beta_raw = info.get("beta")
        beta = fmt_round(beta_raw) if beta_raw is not None else "N/A"

        result = {
            "symbol": symbol,
            "company_name": info.get("longName", symbol),
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "eps": eps,
            "roe": roe,
            "roa": roa,
            "debt_to_equity": debt_to_equity,
            "div_yield": div_yield,
            "market_cap": market_cap_raw if market_cap_raw else "N/A",
            "market_cap_cr": market_cap_cr,
            "beta": beta,
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
        }

        _cache[key] = result
        return result

    except Exception as e:

        logger.error("get_fundamental_analysis failed %s", e)

        return {
            "error": "Unable to fetch fundamentals"
        }


# -------------------------------------------------------------
# COMPARE STOCKS
# -------------------------------------------------------------
def compare_stocks(symbols: list) -> pd.DataFrame:

    data = []

    for symbol in symbols:

        price = get_stock_price(symbol)

        if "error" not in price:

            data.append({
                "Symbol": symbol,
                "Price": price["current_price"],
                "Change %": price["change_pct"]
            })

    return pd.DataFrame(data)


# -------------------------------------------------------------
# SIP CALCULATOR
# -------------------------------------------------------------
def calculate_sip(monthly_amount: float, annual_return_pct: float, years: int):

    r = annual_return_pct / 100 / 12
    n = years * 12

    if r == 0:
        future_value = monthly_amount * n
    else:
        future_value = monthly_amount * (((1 + r) ** n - 1) / r) * (1 + r)

    total_invested = monthly_amount * n
    wealth_gained = future_value - total_invested
    absolute_return_pct = (wealth_gained / total_invested) * 100 if total_invested else 0

    yearly_data = []

    for year in range(1, years + 1):
        months = year * 12
        if r == 0:
            value = monthly_amount * months
        else:
            value = monthly_amount * (((1 + r) ** months - 1) / r) * (1 + r)

        yearly_data.append({
            "year": year,
            "invested": monthly_amount * months,
            "value": value
        })

    return {
        "total_invested": round(total_invested, 2),
        "estimated_returns": round(future_value, 2),
        "wealth_gained": round(wealth_gained, 2),
        "absolute_return_pct": round(absolute_return_pct, 2),
        "yearly_breakdown": yearly_data
    }

def calculate_tax_implications(buy_price: float, sell_price: float,
                                quantity: int, holding_days: int) -> dict:

    total_buy = buy_price * quantity
    total_sell = sell_price * quantity
    gross_gain = total_sell - total_buy

    # return percentage
    return_pct = (gross_gain / total_buy) * 100 if total_buy else 0

    if holding_days < 365:

        tax_rate = 0.20
        tax_type = "STCG (Short Term Capital Gain)"
        tax = max(gross_gain * tax_rate, 0)
        exemption = 0

    else:

        tax_rate = 0.125
        tax_type = "LTCG (Long Term Capital Gain)"

        exemption = 125000
        taxable_gain = max(gross_gain - exemption, 0)
        tax = taxable_gain * tax_rate

    return {
        "buy_price": buy_price,
        "sell_price": sell_price,
        "quantity": quantity,

        "total_investment": round(total_buy, 2),
        "total_proceeds": round(total_sell, 2),

        "gross_gain_loss": round(gross_gain, 2),
        "return_pct": round(return_pct, 2),

        "holding_days": holding_days,
        "tax_type": tax_type,
        "tax_rate_pct": tax_rate * 100,
        "ltcg_exemption": exemption,

        "tax_payable": round(tax, 2),
        "net_gain_after_tax": round(gross_gain - tax, 2)
    }
