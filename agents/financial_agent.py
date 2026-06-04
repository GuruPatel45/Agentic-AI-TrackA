# ============================================================
# agents/financial_agent.py
# LangChain financial agent with memory and tool integration
# ============================================================

import re
import json
import warnings
import datetime
import logging
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool

from llm import get_llm
from prompts import (
    FINANCIAL_AGENT_SYSTEM, get_chat_prompt, get_stock_analysis_prompt,
    get_comparison_prompt, get_portfolio_prompt, get_news_summary_prompt,
    PROFESSIONAL_ANALYSIS_STRUCTURE
)
from tools.stock_tools import (
    get_stock_price, get_historical_data, calculate_technical_indicators,
    get_fundamental_analysis, compare_stocks,
)
from tools.ai_signals import get_top_movers
from tools.news_tools import get_news_with_sentiment
from database.db_manager import save_analysis
from ddgs import DDGS

def _ddg_search(query: str) -> str:
    """Internal helper to perform search using the new ddgs package."""
    try:
        results_text = []
        queries = [query]
        # If it's a price query, add a more specific variant
        if "price" in query.lower():
            queries.append(query + " historical data table")
            
        with DDGS() as ddgs:
            for q in queries:
                res = list(ddgs.text(q, max_results=8))
                if res:
                    results_text.extend([f"{r.get('title', '')}: {r.get('body', '')}" for r in res])
            
            if not results_text:
                return "No search results found."
            return "\n\n".join(results_text[:12])
    except Exception as e:
        return f"Search error: {str(e)}"

@tool
def search_market_info(query: str) -> str:
    """Search the web for real-time market information, index constituents (like Nifty 50 stocks), latest news, or general financial questions. Use this when you are unsure about the current state of the market or need to fact-check your knowledge."""
    return _ddg_search(query)

@tool
def fetch_nse_live_quote(symbol: str) -> str:
    """Fetch RAW REAL-TIME data directly from NSE India for a specific stock (e.g. RELIANCE, TCS). This provides the official exchange quote, depth, and unadjusted price."""
    try:
        from nsepython import nse_quote_meta
        # nsepython nse_quote_meta returns official exchange JSON
        data = nse_quote_meta(symbol.upper().split(".")[0])
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error fetching from NSE: {e}. Try fetch_historical_prices as fallback."

@tool
def fetch_bse_live_quote(symbol: str) -> str:
    """Fetch RAW REAL-TIME data from BSE India (Bombay Stock Exchange). Use symbols ending in .BO."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        # Filter to essential live fields to prove it's raw
        live_fields = {
            "symbol": symbol,
            "currentPrice": info.get("currentPrice"),
            "regularMarketPrice": info.get("regularMarketPrice"),
            "previousClose": info.get("previousClose"),
            "dayLow": info.get("dayLow"),
            "dayHigh": info.get("dayHigh"),
            "volume": info.get("volume"),
            "exchange": info.get("exchange")
        }
        return json.dumps(live_fields, indent=2)
    except Exception as e:
        return f"Error fetching from BSE: {e}"

@tool
def fetch_stock_price_on_date(symbol: str, target_date: str) -> str:
    """Fetch the exact closing and opening stock price for a stock or index on a specific historical date (Format: DD-MM-YYYY, e.g., 27-08-2020). Use this for any question asking for a stock price on a specific date in the past."""
    symbol = symbol.strip().upper()
    if not symbol.startswith("^") and not symbol.endswith((".NS", ".BO")):
        symbol += ".NS"
    res = get_stock_price(symbol, target_date=target_date)
    if "error" in res:
        return f"Error: {res['error']}"
    return f"On {target_date}, {res.get('company_name', symbol)} ({symbol}) price was: Open: ₹{res.get('open_price')}, Close/Current: ₹{res.get('current_price')}"

@tool
def fetch_current_stock_data(symbol: str) -> str:
    """Fetch real-time data for a stock or index (Nifty 50: ^NSEI, Sensex: ^BSESN) directly synchronized with NSE/BSE systems. Use this for current prices."""
    symbol = symbol.strip().upper()
    # Map common names to symbols
    mapping = {"NIFTY": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK", "NIFTY 50": "^NSEI"}
    symbol = mapping.get(symbol, symbol)
    
    if not symbol.startswith("^") and not symbol.endswith((".NS", ".BO")):
        symbol += ".NS"
    data = get_stock_price(symbol)
    if "error" in data:
        return data["error"]
    
    # Clean up None values
    def clean(val): return val if val is not None and val != "N/A" else "N/A"
    
    return (
        f"Symbol: {data.get('symbol')} | Name: {data.get('company_name')} | Sector: {clean(data.get('sector'))}\n"
        f"Price: ₹{clean(data.get('current_price'))} | Change: {clean(data.get('change_pct'))}%\n"
        f"Prev Close: ₹{clean(data.get('previous_close'))} | Day High: ₹{clean(data.get('day_high'))} | Day Low: ₹{clean(data.get('day_low'))}\n"
        f"Market Cap: {clean(data.get('market_cap'))} | P/E: {clean(data.get('pe_ratio'))} | Div Yield: {clean(data.get('div_yield'))}%\n"
        f"52W High: ₹{clean(data.get('52_week_high'))} | 52W Low: ₹{clean(data.get('52_week_low'))} | Vol: {clean(data.get('volume'))}\n"
        f"{data.get('search_context', '')}"
    )

@tool
def fetch_historical_prices(symbol: str, period: str = "1mo") -> str:
    """Fetch historical price data for a stock or index (Nifty 50: ^NSEI) from official NSE/BSE archives. Use this for 'closing price on [DATE]' or trend analysis."""
    symbol = symbol.strip().upper()
    mapping = {"NIFTY": "^NSEI", "SENSEX": "^BSESN", "BANKNIFTY": "^NSEBANK", "NIFTY 50": "^NSEI"}
    symbol = mapping.get(symbol, symbol)
    
    if not symbol.startswith("^") and not symbol.endswith((".NS", ".BO")):
        symbol += ".NS"
    df = get_historical_data(symbol, period=period)
    if df.empty:
        return f"No historical data found for {symbol} in period {period}."
    
    # Return the full requested data
    summary = df.to_string()
    return f"Historical Data for {symbol} ({period}):\n{summary}"

@tool
def fetch_stock_fundamentals(symbol: str) -> str:
    """Fetch fundamental metrics for an Indian stock (P/E, P/B, ROE, Debt/Equity, Beta, etc.). Use this for questions about company health or valuation."""
    symbol = symbol.strip().upper()
    if not symbol.endswith((".NS", ".BO")):
        symbol += ".NS"
    data = get_fundamental_analysis(symbol)
    if "error" in data:
        return data["error"]
    return f"Fundamentals for {data.get('company_name')} ({data.get('symbol')}): P/E Ratio: {data.get('pe_ratio')}, P/B Ratio: {data.get('pb_ratio')}, ROE: {data.get('roe')}, Debt/Equity: {data.get('debt_to_equity')}, Beta: {data.get('beta')}, Sector: {data.get('sector')}"

@tool
def fetch_stock_news(symbol: str) -> str:
    """Fetch recent news articles and overall sentiment for a stock. Use this for questions about latest updates, events, or market sentiment."""
    symbol = symbol.strip().upper()
    if not symbol.endswith((".NS", ".BO")):
        symbol += ".NS"
    data = get_news_with_sentiment(symbol)
    headlines = "\n".join([f"- {a['title']} ({a['source']})" for a in data.get('articles', [])[:5]])
    return f"News Sentiment for {symbol}: {data.get('overall_sentiment')}. Recent Headlines:\n{headlines}"

@tool
def fetch_company_profile(symbol: str) -> str:
    """Fetch the company profile, including business summary, key executives (owners/officers), website, and industry. Use this for 'Who owns...', 'What does [COMPANY] do?', or corporate info questions."""
    symbol = symbol.strip().upper()
    if not symbol.startswith("^") and not symbol.endswith((".NS", ".BO")):
        symbol += ".NS"
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        summary = info.get("longBusinessSummary", "N/A")
        officers = info.get("companyOfficers", [])
        officer_txt = "\n".join([f"- {o.get('name')} ({o.get('title')})" for o in officers[:5]]) if officers else "N/A"
        
        return (
            f"### COMPANY PROFILE: {info.get('longName', symbol)} ###\n"
            f"Sector: {info.get('sector', 'N/A')} | Industry: {info.get('industry', 'N/A')}\n"
            f"Website: {info.get('website', 'N/A')}\n\n"
            f"BUSINESS SUMMARY:\n{summary[:800]}...\n\n"
            f"KEY EXECUTIVES/OFFICERS:\n{officer_txt}"
        )
    except Exception as e:
        return f"Error fetching profile: {e}"

@tool
def fetch_technical_indicators(symbol: str) -> str:
    """Fetch technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands) to understand price trends and momentum."""
    symbol = symbol.strip().upper()
    if not symbol.endswith((".NS", ".BO")):
        symbol += ".NS"
    df = get_historical_data(symbol, period="6mo")
    if df.empty:
        return f"No historical data found for {symbol}"
    df_with_ind = calculate_technical_indicators(df)
    last = df_with_ind.iloc[-1]
    return f"Technicals for {symbol}: RSI: {last.get('RSI')}, MACD: {last.get('MACD')}, SMA_50: {last.get('SMA_50')}, Trend: {'Bullish' if last['Close'] > last.get('SMA_50', 0) else 'Bearish'}"

@tool
def fetch_top_movers(target_date: str = None) -> str:
    """Fetch the top 5 gainers and top 5 losers in the Indian market. Use this for ANY question about market trends, gainers, losers, or performance. CRITICAL: Use the EXACT prices and percentages provided here. DO NOT guess or hallucinate prices."""
    try:
        data = get_top_movers(target_date)
        date_str = f" for {target_date}" if target_date else " Today"
        gainers = "\n".join([f"- {m['company']} ({m['symbol']}): ₹{m['price']:,.2f} | +{m['change_pct']}%" for m in data.get('gainers', [])])
        losers = "\n".join([f"- {m['company']} ({m['symbol']}): ₹{m['price']:,.2f} | {m['change_pct']}%" for m in data.get('losers', [])])
        
        if not gainers and not losers:
            return f"Unable to fetch mover data currently for {date_str}. Data might be unavailable."
            
        source = data.get('source', 'Unknown')
        return f"### VERIFIED TOP MOVERS DATA (Source: {source}) ###\n\nTop Gainers{date_str}:\n{gainers}\n\nTop Losers{date_str}:\n{losers}\n\nINSTRUCTION: Use the EXACT prices above. Do NOT hallucinate."
    except Exception as e:
        return f"Failed to fetch top movers: {str(e)}"

class FinancialAgent:
    """
    Main AI financial agent.

    Capabilities:
    - Conversational Q&A about Indian stocks (with memory)
    - Full stock analysis combining price, fundamentals, technicals, news
    - Multi-stock comparison
    - Portfolio analysis
    - News summarization

    Architecture:
    - LLM: Gemini or OpenAI (configured via .env)
    - Memory: InMemoryChatMessageHistory (last 10 exchanges)
    - Prompts: Specialized templates per task
    """

    def __init__(self):
        self.llm = get_llm()
        self._chat_history = InMemoryChatMessageHistory()
        self.tools = [
            fetch_current_stock_data, 
            fetch_historical_prices,
            fetch_stock_price_on_date,
            fetch_stock_fundamentals, 
            fetch_stock_news,
            fetch_technical_indicators,
            fetch_top_movers,
            search_market_info,
            fetch_nse_live_quote,
            fetch_bse_live_quote,
            fetch_company_profile
        ]

    def _trim_history(self, k=10):
        """Keep only last k*2 messages (k human + k AI)."""
        messages = self._chat_history.messages
        if len(messages) > k * 2:
            self._chat_history.clear()
            for msg in messages[-(k * 2):]:
                self._chat_history.add_message(msg)

    def chat(self, user_message: str) -> str:
        # ============================================================
        # PIPELINE FLOW:
        # User Question → Frontend Chat UI → Backend API → Query Understanding → Stock/Ticker Extraction → yfinance Data Fetch → Technical Indicator Engine → Prompt Builder → Gemini API → Response Formatter → Frontend Display
        # ============================================================
        
        logging.info("Backend API Layer: Received user question in chat endpoint")
        
        try:
            now = datetime.datetime.now().strftime("%d %B %Y")
            processed_message = user_message.strip()
            
            # -------------------------------------------------------------
            # STEP 1: Query Understanding Layer
            # -------------------------------------------------------------
            is_historical = False
            target_date_str = None
            
            # Textual and numerical date extraction patterns (e.g. "24 august 2025", "27-08-2020", etc.)
            date_match = re.search(
                r'(\d{1,2})[-/\s](january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec|\d{1,2})[-/\s](\d{4})', 
                processed_message, 
                re.IGNORECASE
            )
            if date_match:
                is_historical = True
                day = date_match.group(1)
                month = date_match.group(2)
                year = date_match.group(3)
                month_map = {
                    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
                    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12",
                    "january": "01", "february": "02", "march": "03", "april": "04", "june": "06",
                    "july": "07", "august": "08", "september": "09", "october": "10", "november": "11", "december": "12"
                }
                m_str = month.lower()
                month_digit = month_map.get(m_str, month.zfill(2))
                target_date_str = f"{day.zfill(2)}-{month_digit}-{year}"
                logging.info(f"Query Understanding: Target date {target_date_str} extracted.")
            else:
                logging.info("Query Understanding: Live or general market intent detected.")

            # -------------------------------------------------------------
            # STEP 2: Stock/Ticker Extraction
            # -------------------------------------------------------------
            symbol = None
            common_symbols = {
                "reliance": "RELIANCE.NS", "hal": "HAL.NS", "tcs": "TCS.NS", "infosys": "INFY.NS", 
                "wipro": "WIPRO.NS", "hdfc": "HDFCBANK.NS", "icici": "ICICIBANK.NS", "sbi": "SBIN.NS",
                "tata motors": "TATAMOTORS.NS", "itc": "ITC.NS", "adani": "ADANIENT.NS"
            }
            words = processed_message.lower()
            for key, sym in common_symbols.items():
                if key in words:
                    symbol = sym
                    break
            
            if not symbol:
                symbol_match = re.search(r'\b([A-Z]{2,10}(?:\.[A-Z]{2,4})?)\b', processed_message)
                if symbol_match:
                    symbol = symbol_match.group(1).upper()
                    if not symbol.endswith(".NS") and symbol not in ["BSE", "NSE"]:
                        symbol = symbol + ".NS"
            
            if not symbol:
                symbol = "HAL.NS"  # Default safe fallback
                logging.info("Stock Extraction: No symbol matched, falling back to HAL.NS")
            else:
                logging.info(f"Stock Extraction: Extracted symbol {symbol}")

            # -------------------------------------------------------------
            # STEP 3: yfinance Data Fetch Layer
            # -------------------------------------------------------------
            raw_data = None
            logging.info(f"yfinance Data Fetch: Fetching data for {symbol} (Target Date: {target_date_str})")
            try:
                if is_historical and target_date_str:
                    raw_data = get_stock_price(symbol, target_date=target_date_str)
                else:
                    raw_data = get_stock_price(symbol)
            except Exception as fe:
                logging.error(f"yfinance Fetch Failed: {fe}")
                raw_data = {"error": str(fe)}

            # -------------------------------------------------------------
            # STEP 4: Technical Indicator Engine
            # -------------------------------------------------------------
            technicals_str = "Bypassed (Not requested or not needed for basic lookup)"
            if "technicals" in words or "indicators" in words or "rsi" in words or "macd" in words or "trend" in words:
                logging.info("Technical Indicator Engine: Calculating indicators")
                try:
                    df = get_historical_data(symbol, period="3mo")
                    if not df.empty:
                        df_with_ind = calculate_technical_indicators(df)
                        last_row = df_with_ind.iloc[-1]
                        technicals_str = f"RSI: {last_row.get('RSI', 'N/A'):.2f}, MACD: {last_row.get('MACD', 'N/A'):.2f}, SMA_50: {last_row.get('SMA_50', 'N/A'):.2f}, Close: {last_row.get('Close', 'N/A'):.2f}"
                except Exception as te:
                    logging.error(f"Technical Indicator Calculation Failed: {te}")
                    technicals_str = f"Error: {str(te)}"

            # -------------------------------------------------------------
            # STEP 5: Prompt Builder Layer
            # -------------------------------------------------------------
            logging.info("Prompt Builder: Formatting prompt context")
            history_messages = self._chat_history.messages
            cleaned_history = []
            for msg in history_messages[-4:]:
                cleaned_history.append(f"{'User' if isinstance(msg, HumanMessage) else 'Agent'}: {msg.content}")
            history_context = "\n".join(cleaned_history)

            structured_context = f"""
You are FinSaarthi 🇮🇳 — a highly experienced investment strategist and equity strategist.
Analyze the user's query and provide a direct, highly accurate, and concise answer. 
You have access to the following backend system data for specific stock queries. If the user asks about this specific stock, prioritize this data. If the user asks a general finance or market question (like "What is SIP?", "What is Nifty 50?"), use your extensive financial knowledge to answer it naturally.

[VERIFIED SYSTEM PIPELINE DATA]
- symbol: {symbol}
- target_date: {target_date_str if target_date_str else "N/A"}
- historical_data_records: {json.dumps(raw_data, indent=2) if raw_data else "No historical records"}
- technical_indicator_state: {technicals_str}
- system_datetime: {now}

[CHAT HISTORY CONTEXT]
{history_context}

User Question: {user_message}

CRITICAL INSTRUCTIONS:
1. Return a direct, concise, and highly professional answer.
2. If the user asked for a price on a date that falls on a weekend, state clearly that it was a holiday/weekend and provide the last available trading price.
3. Do NOT mention the backend pipeline details, code structures, or the fact that data was "provided" to you. Keep it completely natural, human-like, and strategically sound.
4. For general finance definitions, strategies, or concepts (e.g. SIP, Mutual Funds, Options), just explain them using your general knowledge without apologizing for missing system data.
"""

            # -------------------------------------------------------------
            # STEP 6: Gemini API Execution Layer
            # -------------------------------------------------------------
            logging.info("Gemini API: Invoking model chain")
            direct_prompt = ChatPromptTemplate.from_messages([
                ("human", "{input}"),
            ])
            chain = direct_prompt | self.llm
            response_obj = chain.invoke({"input": structured_context})
            output = str(response_obj.content)

            # -------------------------------------------------------------
            # STEP 7: Response Formatter Layer
            # -------------------------------------------------------------
            logging.info("Response Formatter: Formatting generated response")
            output = re.sub(r'(?i)[>\s]*\*\*?Thought:.*?\*\*?\n?', '', output)
            output = re.sub(r'(?i)[>\s]*\*\*?Action:.*?\*\*?\n?', '', output)
            output = re.sub(r'(?i)thought:.*?(?:\n|$)', '', output)
            output = output.strip()

            # Persist in chat memory
            self._chat_history.add_user_message(user_message)
            self._chat_history.add_ai_message(output)
            
            # Trim memory
            if len(self._chat_history.messages) > 10:
                self._chat_history.messages = self._chat_history.messages[-10:]

            # -------------------------------------------------------------
            # STEP 8: Frontend Display (handled by returning output to app.py)
            # -------------------------------------------------------------
            return output

        except Exception as e:
            logging.error(f"Execution Pipeline Failed: {str(e)}")
            return f"❌ Pipeline Execution Error: {str(e)}"

    def analyze_stock(self, symbol: str) -> dict:
        """
        Full multi-dimensional stock analysis.

        Gathers data from all sources, runs AI interpretation,
        and returns structured results including AI commentary.

        Args:
            symbol: NSE stock symbol e.g. 'RELIANCE.NS'

        Returns:
            dict with price_data, fundamental_data, technical_summary,
                  news_data, ai_analysis, raw_df (for charting)
        """
        # Normalize symbol
        symbol = symbol.strip().upper()
        if not symbol.endswith((".NS", ".BO")):
            symbol += ".NS"  # Default to NSE

        # Gather all data
        price_data = get_stock_price(symbol)
        if "error" in price_data:
            return {"error": price_data["error"]}

        fundamental_data = get_fundamental_analysis(symbol)
        company_name = price_data.get("company_name", symbol)
        news_data = get_news_with_sentiment(symbol, company_name)

        # Technical indicators
        df = get_historical_data(symbol, period="6mo")
        technical_summary = {}
        if not df.empty:
            df_with_indicators = calculate_technical_indicators(df)
            last = df_with_indicators.iloc[-1]
            technical_summary = {
                "current_price": round(float(last["Close"]), 2),
                "sma_20": round(float(last.get("SMA_20", 0) or 0), 2),
                "sma_50": round(float(last.get("SMA_50", 0) or 0), 2),
                "ema_20": round(float(last.get("EMA_20", 0) or 0), 2),
                "rsi": round(float(last.get("RSI", 0) or 0), 2),
                "macd": round(float(last.get("MACD", 0) or 0), 2),
                "macd_signal": round(float(last.get("MACD_Signal", 0) or 0), 2),
                "bb_upper": round(float(last.get("BB_Upper", 0) or 0), 2),
                "bb_lower": round(float(last.get("BB_Lower", 0) or 0), 2),
                "trend": "Bullish" if last["Close"] > (last.get("SMA_50") or last["Close"]) else "Bearish",
                "rsi_signal": (
                    "Overbought (>70)" if (last.get("RSI") or 0) > 70
                    else "Oversold (<30)" if (last.get("RSI") or 0) < 30
                    else "Neutral (30-70)"
                ),
            }

        # Generate AI analysis
        ai_analysis = self._generate_stock_analysis(
            symbol, company_name, price_data, fundamental_data,
            technical_summary, news_data
        )

        # Save to history
        save_analysis(symbol, "full_analysis", {"price": price_data, "fundamentals": fundamental_data})

        return {
            "symbol": symbol,
            "company_name": company_name,
            "price_data": price_data,
            "fundamental_data": fundamental_data,
            "technical_summary": technical_summary,
            "news_data": news_data,
            "ai_analysis": ai_analysis,
            "raw_df": df,  # For Plotly charts
        }

    def _generate_stock_analysis(self, symbol, company_name, price_data,
                                  fundamental_data, technical_summary, news_data) -> str:
        """Internal: Call LLM to generate analysis narrative."""
        try:
            prompt = get_stock_analysis_prompt()
            chain = prompt | self.llm

            # Format news articles for the prompt
            articles_text = "\n".join([
                f"- [{a.get('published_at', '')}] {a.get('title', '')} "
                f"(Sentiment: {a.get('sentiment', {}).get('label', 'N/A')})"
                for a in news_data.get("articles", [])[:5]
            ])

            response = chain.invoke({
                "symbol": symbol,
                "company_name": company_name,
                "price_data": json.dumps(price_data, default=str, indent=2),
                "fundamental_data": json.dumps(fundamental_data, default=str, indent=2),
                "technical_data": json.dumps(technical_summary, default=str, indent=2),
                "news_sentiment": f"{news_data.get('summary', '')}\n\nRecent Headlines:\n{articles_text}",
            })
            return response.content
        except Exception as e:
            return f"AI analysis unavailable: {str(e)}"

    def compare_stocks_with_ai(self, symbols: list) -> dict:
        """
        Compare multiple stocks and generate AI commentary.

        Args:
            symbols: List of stock symbols e.g. ['TCS.NS', 'INFY.NS']

        Returns:
            dict with comparison_df and ai_commentary
        """
        try:
            df = compare_stocks(symbols)
            if df.empty:
                return {"error": "Could not fetch data for comparison"}

            # Infer sector from first stock
            sector = "Indian Equity"
            try:
                info = get_fundamental_analysis(symbols[0])
                sector = info.get("sector", "Indian Equity")
            except Exception:
                pass

            # AI commentary
            prompt = get_comparison_prompt()
            chain = prompt | self.llm
            response = chain.invoke({
                "comparison_data": df.to_string(index=False),
                "sector": sector,
            })

            return {
                "comparison_df": df,
                "ai_commentary": response.content,
            }
        except Exception as e:
            return {"error": str(e)}

    def analyze_portfolio_with_ai(self, portfolio_data: list, current_prices: dict) -> dict:
        """
        Analyze user portfolio and provide AI insights.

        Args:
            portfolio_data: List of holdings from database
            current_prices: Dict of {symbol: current_price}

        Returns:
            dict with portfolio_df, metrics, and ai_analysis
        """
        try:
            import pandas as pd

            rows = []
            total_invested = 0
            total_current = 0

            for holding in portfolio_data:
                symbol = holding["symbol"]
                buy_price = holding["buy_price"]
                quantity = holding["quantity"]
                current_price = current_prices.get(symbol, buy_price)

                invested = buy_price * quantity
                current_val = current_price * quantity
                pnl = current_val - invested
                pnl_pct = (pnl / invested) * 100 if invested else 0

                total_invested += invested
                total_current += current_val

                rows.append({
                    "Symbol": symbol,
                    "Company": holding.get("company_name", symbol),
                    "Qty": quantity,
                    "Buy Price (₹)": round(buy_price, 2),
                    "Current (₹)": round(current_price, 2),
                    "Invested (₹)": round(invested, 2),
                    "Value (₹)": round(current_val, 2),
                    "P&L (₹)": round(pnl, 2),
                    "Return %": round(pnl_pct, 2),
                })

            df = pd.DataFrame(rows)
            total_pnl = total_current - total_invested
            total_pnl_pct = (total_pnl / total_invested) * 100 if total_invested else 0

            # AI analysis
            prompt = get_portfolio_prompt()
            chain = prompt | self.llm
            response = chain.invoke({
                "portfolio_data": df.to_string(index=False),
                "total_invested": f"{total_invested:,.2f}",
                "current_value": f"{total_current:,.2f}",
                "pnl": f"{total_pnl:,.2f}",
                "pnl_pct": f"{total_pnl_pct:.2f}",
            })

            return {
                "portfolio_df": df,
                "total_invested": total_invested,
                "current_value": total_current,
                "pnl": total_pnl,
                "pnl_pct": total_pnl_pct,
                "ai_analysis": response.content,
            }

        except Exception as e:
            return {"error": str(e)}

    def clear_memory(self):
        """Clear conversation history."""
        self._chat_history.clear()
