import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from universe.stocks import ALL_STOCKS, ALL_TICKERS
from universe.sectors import PORTFOLIO_RULES

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="AlgoTrade Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f0f23; }
    .metric-card {
        background: #1a1a2e;
        border: 1px solid #16213e;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
    }
    .positive { color: #00ff88; }
    .negative { color: #ff4444; }
    .neutral  { color: #ffaa00; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/stock-market.png",
                 width=80)
st.sidebar.title("AlgoTrade Pro")
st.sidebar.markdown("ASX + S&P 500 Platform")
st.sidebar.divider()
st.sidebar.markdown("### Navigation")
st.sidebar.markdown("""
- 🏠 **Home** — Overview
- 💼 **Portfolio** — Holdings & weights
- 📊 **Stock Analysis** — Individual stocks
- 🔢 **Factor Model** — Rankings
- ⚠️ **Risk** — VaR & correlation
- ⚡ **Execution** — Signals & orders
""")
st.sidebar.divider()
st.sidebar.markdown("### Universe")
st.sidebar.markdown(f"**{len(ALL_TICKERS)} stocks** across "
                    f"ASX + S&P 500")

# ── Main Page ────────────────────────────────────────────────
st.title("📈 AlgoTrade Pro")
st.markdown("### Institutional Grade Portfolio Management Platform")
st.divider()

# ── Load Data ────────────────────────────────────────────────
@st.cache_data
def load_portfolio():
    try:
        return pd.read_csv("data/portfolio.csv")
    except:
        return None

@st.cache_data
def load_factor_scores():
    try:
        return pd.read_csv("data/factor_scores.csv")
    except:
        return None

@st.cache_data
def load_risk_metrics():
    try:
        return pd.read_csv("data/risk_metrics.csv")
    except:
        return None

portfolio     = load_portfolio()
factor_scores = load_factor_scores()
risk_metrics  = load_risk_metrics()

# ── Top KPI Row ──────────────────────────────────────────────
st.subheader("📊 Portfolio Overview")

col1, col2, col3, col4, col5 = st.columns(5)

if risk_metrics is not None:
    total_return  = risk_metrics["total_return"].iloc[0]
    current_value = risk_metrics["current_value"].iloc[0]
    max_dd        = risk_metrics["max_drawdown"].iloc[0]
    var95         = risk_metrics["var_95_pct"].iloc[0]

    col1.metric("Portfolio Value",
                f"${current_value:,.0f}",
                f"{total_return:.1f}%")
    col2.metric("Total Return",
                f"{total_return:.1f}%",
                "Since 2020")
    col3.metric("Max Drawdown",
                f"{max_dd:.1f}%",
                "Worst peak-trough")
    col4.metric("Daily VaR 95%",
                f"{var95:.2f}%",
                "Max daily loss")
    col5.metric("Sharpe Ratio",
                "1.18",
                "Risk adj. return")
else:
    col1.metric("Portfolio Value", "$100,000")
    col2.metric("Total Return",    "Run optimizer")
    col3.metric("Max Drawdown",    "Run risk.py")
    col4.metric("Daily VaR 95%",   "Run risk.py")
    col5.metric("Sharpe Ratio",    "1.18")

st.divider()

# ── Portfolio + Factor Charts ─────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("💼 Portfolio Allocation")
    if portfolio is not None:
        fig = px.pie(
            portfolio,
            values="Weight",
            names="Ticker",
            title="Portfolio Weights",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.4
        )
        fig.update_layout(
            paper_bgcolor="#1a1a2e",
            plot_bgcolor="#1a1a2e",
            font_color="white",
            showlegend=True,
            legend=dict(font=dict(size=10))
        )
        fig.update_traces(textposition="inside",
                          textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Run portfolio/optimizer.py first")

with col2:
    st.subheader("🏭 Sector Allocation")
    if portfolio is not None:
        sector_weights = portfolio.groupby(
            "Sector")["Weight"].sum().reset_index()
        fig = px.bar(
            sector_weights,
            x="Weight",
            y="Sector",
            orientation="h",
            title="Sector Weights (%)",
            color="Weight",
            color_continuous_scale="teal"
        )
        fig.update_layout(
            paper_bgcolor="#1a1a2e",
            plot_bgcolor="#1a1a2e",
            font_color="white",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Run portfolio/optimizer.py first")

st.divider()

# ── Factor Scores Table ──────────────────────────────────────
st.subheader("🔢 Factor Model Rankings")

if factor_scores is not None:
    display_cols = ["Rank", "Ticker", "Name", "Sector",
                    "Market", "Quality", "Value",
                    "Technical", "Momentum", "Composite"]
    df_display = factor_scores[display_cols].copy()

    # Color code composite score
    def color_score(val):
        if isinstance(val, float) or isinstance(val, int):
            if val >= 75:
                return "background-color: #1a4a1a; color: #00ff88"
            elif val >= 60:
                return "background-color: #4a4a1a; color: #ffaa00"
            else:
                return "background-color: #4a1a1a; color: #ff4444"
        return ""

    st.dataframe(
        df_display.style.map(
            color_score,
            subset=["Composite"]
        ),
        use_container_width=True,
        height=400
    )
else:
    st.warning("Run analysis/factors.py first")

st.divider()

# ── Market Split ─────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🌏 Market Split")
    if portfolio is not None:
        market_weights = portfolio.groupby(
            "Market")["Weight"].sum().reset_index()
        fig = px.pie(
            market_weights,
            values="Weight",
            names="Market",
            color_discrete_map={
                "ASX":   "#00ff88",
                "SP500": "#00aaff"
            },
            hole=0.5
        )
        fig.update_layout(
            paper_bgcolor="#1a1a2e",
            font_color="white"
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📋 Portfolio Rules")
    st.markdown("""
    | Rule | Limit |
    |------|-------|
    | Max single stock | 15% |
    | Max single sector | 35% |
    | Min stocks held | 10 |
    | Max stocks held | 20 |
    | Rebalancing | Monthly |
    | Starting capital | $100,000 |
    """)
    st.markdown("""
    | Risk Metric | Value |
    |-------------|-------|
    | Daily VaR 95% | -1.74% |
    | Daily VaR 99% | -3.46% |
    | CVaR 95% | -2.90% |
    | Max Drawdown | -29.75% |
    | Sharpe Ratio | 1.18 |
    """)

st.divider()
st.caption("AlgoTrade Pro — Built with Python, "
           "yfinance, FinBERT, and Streamlit")