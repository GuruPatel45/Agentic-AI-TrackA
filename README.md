# 📈 FinSaarthi v2.0 — AI Indian Stock Intelligence Dashboard

> **AI-Powered Financial Intelligence for Indian Markets** — Professional-grade stock analysis dashboard with AI signals, market mood analysis, portfolio risk assessment, and automated market briefs.

## 🌟 Live Demo
Experience the fully deployed version of the application here:
**[FinSaarthi Live Deployment](https://agenticai-project-tracka-uzf4xslbwafhmbuw374ijk.streamlit.app/)**

## ✨ Features

- **📊 Dashboard**: Real-time pulse of the market with Nifty 50, Sensex tracking, Market Mood indicators, Sector Heatmap, and 52-Week Pulse.
- **📈 Stock Analysis**: Technical and fundamental metrics, AI-driven buy/hold/sell signals with confidence scoring, and interactive Plotly charts.
- **⚖️ Compare Stocks**: Multi-stock signal comparison and AI narrative analysis.
- **📰 News & Sentiment**: Aggregated financial news with natural language sentiment scoring.
- **💼 Portfolio Tracker**: P&L tracking, portfolio risk assessment, diversification scoring, and performance visualization.
- **⭐ Watchlist**: Curate and monitor your favorite stocks with real-time AI signal indicators.
- **📋 Market Brief**: Automated daily summaries and sector performance insights.
- **🧮 Calculators**: Built-in SIP calculator and Tax Implications calculator for planning investments.
- **💬 AI Chat**: Interactive financial agent powered by LangChain and LLMs to answer your market-related queries.

## 🏗️ Technology Stack

- **Frontend**: Streamlit, Plotly (for interactive charting)
- **AI/LLM**: LangChain, Groq, Google GenAI, OpenAI
- **Data & Finance**: yfinance, pandas, textblob, vaderSentiment, NewsAPI
- **Backend/DB**: SQLite, Python 3.11+

## 🚀 Quick Start (Local Setup)

### Prerequisites
- Python 3.11+
- API Keys: 
  - LLM Provider (Groq is recommended, but OpenAI or Google Gemini can be used)
  - NewsAPI

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Agentic-AI-TrackA-main
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Edit `.env` to include your API keys. Example:
   ```env
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_key_here
   NEWS_API_KEY=your_newsapi_key_here
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 📁 Project Structure

```
.
├── 📁 agents/            # LangChain AI agent logic and market briefs
├── 📁 config/            # Configuration and API management settings
├── 📁 data/              # Local storage directories
├── 📁 database/          # SQLite database operations (Watchlist, Portfolio)
├── 📁 tools/             # yfinance integrations, NewsAPI tools, and AI signal processing
├── 📁 ui/                # UI components, interactive Plotly charts, and custom CSS
├── 📁 views/             # Potential view components or modular pages
├── app.py                # Main Streamlit application entry point
├── llm.py                # LLM provider initialization (Groq, Gemini, OpenAI)
├── prompts.py            # LangChain prompt templates
├── requirements.txt      # Python dependencies
└── utils.py              # Utility functions and formatting helpers
```

## ⚠️ Disclaimer

**Educational Purpose Only**

This application is for educational and informational purposes only. It is not intended to provide financial advice, recommendations, or endorsements. All investment decisions should be made after consulting with qualified financial advisors. The developers and contributors are not responsible for any financial losses incurred through the use of this application.

**Not SEBI Registered**: This is not a SEBI-registered investment advisor or financial planning service.
