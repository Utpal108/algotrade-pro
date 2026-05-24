import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
from universe.stocks import ALL_STOCKS

st.set_page_config(
    page_title="Portfolio — AlgoTrade Pro",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Portfolio Manager")
st.markdown("Optimal portfolio weights and allocations")
st.divider()

# ── Load Data ────────────────────────────────────────────────
@st.cache_data
def load_data():
    portfolio     = pd.read_csv("data/portfolio.csv")
    factor_scores = pd.read_csv("data/factor_scores.csv")
    risk_metrics  = pd.read_csv("data/risk_metrics.csv")
    return portfolio, factor_scores, risk_metrics

try:
    portfolio, factor_scores, risk_metrics = load_data()
except:
    st.error("❌ Run optimizer and risk scripts first")
    st.stop()

capital = 100000

# ── Portfolio Summary ─────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Stocks",    f"{len(portfolio)}")
col2.metric("Total Capital",   f"${capital:,.0f}")
col3.metric("Sharpe Ratio",    "1.18")
col4.metric("Expected Return", "27.97%")

st.divider()

# ── Holdings Table ───────────────────────────────────────────
st.subheader("📋 Current Holdings")

portfolio["Allocation $"] = portfolio["Allocation"].apply(
    lambda x: f"${x:,.0f}")
portfolio["Weight %"] = portfolio["Weight"].apply(
    lambda x: f"{x:.1f}%")

# Signal column based on factor score
def get_signal(score):
    if score >= 75:   return "🟢 BUY"
    elif score >= 60: return "🟡 HOLD"
    else:             return "🔴 SELL"

portfolio["Signal"] = portfolio["Factor Score"].apply(get_signal)

display_cols = ["Ticker", "Name", "Sector", "Market",
                "Weight %", "Allocation $",
                "Factor Score", "Signal"]
st.dataframe(portfolio[display_cols],
             use_container_width=True,
             height=450)

st.divider()

# ── Charts Row ───────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🥧 Portfolio Weights")
    fig = px.pie(
        portfolio,
        values="Weight",
        names="Ticker",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        font_color="white"
    )
    fig.update_traces(textposition="inside",
                      textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Allocation by Stock")
    fig = px.bar(
        portfolio.sort_values("Weight", ascending=True),
        x="Weight",
        y="Ticker",
        orientation="h",
        color="Sector",
        title="Weight % by Stock",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font_color="white"
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Sector and Market breakdown ──────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏭 Sector Breakdown")
    sector_df = portfolio.groupby("Sector").agg(
        Weight=("Weight", "sum"),
        Stocks=("Ticker", "count"),
        Allocation=("Allocation", "sum")
    ).reset_index().sort_values("Weight", ascending=False)

    sector_df["Allocation $"] = sector_df["Allocation"].apply(
        lambda x: f"${x:,.0f}")
    sector_df["Weight %"] = sector_df["Weight"].apply(
        lambda x: f"{x:.1f}%")

    st.dataframe(
        sector_df[["Sector", "Stocks", "Weight %",
                   "Allocation $"]],
        use_container_width=True
    )

with col2:
    st.subheader("🌏 Market Breakdown")
    market_df = portfolio.groupby("Market").agg(
        Weight=("Weight", "sum"),
        Stocks=("Ticker", "count"),
        Allocation=("Allocation", "sum")
    ).reset_index()

    market_df["Allocation $"] = market_df["Allocation"].apply(
        lambda x: f"${x:,.0f}")
    market_df["Weight %"] = market_df["Weight"].apply(
        lambda x: f"{x:.1f}%")

    st.dataframe(
        market_df[["Market", "Stocks", "Weight %",
                   "Allocation $"]],
        use_container_width=True
    )

    st.divider()

    # Market pie chart
    fig = px.pie(
        market_df,
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

st.divider()

# ── Rebalancing Section ──────────────────────────────────────
st.subheader("🔄 Rebalancing")
st.markdown("""
Rebalancing restores your portfolio back to target weights
when individual stocks drift due to price changes.
""")

col1, col2, col3 = st.columns(3)
col1.metric("Rebalance Frequency", "Monthly")
col2.metric("Next Rebalance",      "1st of next month")
col3.metric("Drift Threshold",     "±5% from target")

st.info("💡 Click **Run Optimizer** in the terminal to "
        "regenerate optimal weights with latest prices: "
        "`python portfolio/optimizer.py`")

st.divider()
st.caption("AlgoTrade Pro — Portfolio Manager")