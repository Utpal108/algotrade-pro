import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
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

st.markdown("""
<div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 24px; border-radius: 12px;
            border-left: 4px solid #00ff88; margin-bottom: 20px;'>

<h3 style='color: #00ff88; margin-top: 0;'>
    Institutional Grade Algorithmic Trading Platform
</h3>

<p style='color: #cccccc; font-size: 15px; line-height: 1.7;'>
    <b style='color: white;'>AlgoTrade Pro</b> is a professional quantitative trading platform
    that combines three independent analysis engines into a single unified signal system —
    giving you the same analytical power used by hedge funds and institutional investors,
    built entirely in Python.
</p>

<hr style='border-color: #333; margin: 16px 0;'>

<div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;'>

<div>
<h4 style='color: #00aaff; margin-bottom: 8px;'>📊 What it covers</h4>
<ul style='color: #aaaaaa; font-size: 13px; line-height: 1.8; padding-left: 16px;'>
    <li>20 stocks — ASX + S&P 500</li>
    <li>5 years of historical data</li>
    <li>Real time live price feed</li>
    <li>Daily automated analysis</li>
    <li>Portfolio optimization</li>
</ul>
</div>

<div>
<h4 style='color: #ffaa00; margin-bottom: 8px;'>🔬 How it works</h4>
<ul style='color: #aaaaaa; font-size: 13px; line-height: 1.8; padding-left: 16px;'>
    <li>Technical Analysis + SMC signals</li>
    <li>Fundamental Analysis + DCF valuation</li>
    <li>FinBERT AI news sentiment</li>
    <li>7 Factor Model ranking</li>
    <li>Monte Carlo portfolio optimizer</li>
</ul>
</div>

<div>
<h4 style='color: #ff4444; margin-bottom: 8px;'>⚙️ Risk controls</h4>
<ul style='color: #aaaaaa; font-size: 13px; line-height: 1.8; padding-left: 16px;'>
    <li>Value at Risk (VaR 95% + 99%)</li>
    <li>Max 15% per stock</li>
    <li>Max 35% per sector</li>
    <li>Sharpe Ratio: 1.18</li>
    <li>Correlation matrix monitoring</li>
</ul>
</div>

</div>

<hr style='border-color: #333; margin: 16px 0;'>

<p style='color: #888888; font-size: 12px; margin-bottom: 0;'>
    📍 Universe: CBA.AX · BHP.AX · CSL.AX · WBC.AX · ANZ.AX · WES.AX ·
    TLS.AX · RIO.AX · FMG.AX · MQG.AX · AAPL · MSFT · GOOGL · AMZN ·
    NVDA · JPM · JNJ · XOM · BRK-B · V
</p>

</div>
""", unsafe_allow_html=True)
# Auto refresh every 5 minutes during market hours
from datetime import datetime
current_hour = datetime.now().hour
if 9 <= current_hour <= 16:
    st.empty()
    import time
    st.markdown(
        "<meta http-equiv='refresh' content='300'>",
        unsafe_allow_html=True
    )
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
# ── Live Market Prices ────────────────────────────────────────
st.subheader("📡 Live Market Prices")

@st.cache_data(ttl=300)  # refresh every 5 minutes
def load_live_prices():
    try:
        return pd.read_csv("data/live_prices.csv")
    except:
        return None

live_df = load_live_prices()

if live_df is not None:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🇦🇺 ASX Stocks**")
        asx = live_df[live_df["ticker"].str.contains(
            r"\.AX", regex=True)].copy()
        for _, row in asx.iterrows():
            color = "🟢" if row["change_pct"] >= 0 else "🔴"
            st.markdown(
                f"{color} **{row['ticker']}** &nbsp;&nbsp;"
                f"A${row['price']:.2f} &nbsp;"
                f"`{row['change_pct']:+.2f}%`"
            )

    with col2:
        st.markdown("**🇺🇸 S&P Stocks**")
        sp = live_df[~live_df["ticker"].str.contains(
            r"\.AX", regex=True)].copy()
        for _, row in sp.iterrows():
            color = "🟢" if row["change_pct"] >= 0 else "🔴"
            st.markdown(
                f"{color} **{row['ticker']}** &nbsp;&nbsp;"
                f"${row['price']:.2f} &nbsp;"
                f"`{row['change_pct']:+.2f}%`"
            )

    # Top movers
    st.markdown("**🔥 Top Movers Today**")
    col1, col2, col3, col4, col5 = st.columns(5)
    top5 = live_df.nlargest(5, "change_pct")
    cols = [col1, col2, col3, col4, col5]
    for i, (_, row) in enumerate(top5.iterrows()):
        cols[i].metric(
            row["ticker"],
            f"${row['price']:.2f}",
            f"{row['change_pct']:+.2f}%"
        )

    st.caption(
        f"Last updated: {live_df['timestamp'].iloc[0]} "
        f"| Auto-refreshes every 5 minutes"
    )
else:
    st.info("💡 Run `python data/realtime.py` to load live prices")

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