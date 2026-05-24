import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

st.set_page_config(
    page_title="Factor Model — AlgoTrade Pro",
    page_icon="🔢",
    layout="wide"
)

st.title("🔢 Factor Model")
st.markdown("7 factor ranking system for all 20 stocks")
st.divider()

# ── Load Data ────────────────────────────────────────────────
try:
    df = pd.read_csv("data/factor_scores.csv")
except:
    st.error("Run analysis/factors.py first")
    st.stop()

# ── Factor Explanation ───────────────────────────────────────
with st.expander("📚 About the 7 Factor Model"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Factor 1 — Quality (25% weight)**
        ROE + Profit Margin + Low Debt
        High quality companies consistently outperform

        **Factor 2 — Value (20% weight)**
        P/E + P/B ratios
        Cheap stocks outperform expensive ones long term

        **Factor 3 — Technical (20% weight)**
        RSI + MACD + EMA trend
        Price momentum and trend direction
        """)
    with col2:
        st.markdown("""
        **Factor 4 — Momentum (15% weight)**
        12 month price return
        Winners keep winning (Jegadeesh & Titman 1993)

        **Factor 5 — Dividend (10% weight)**
        Dividend yield
        Income + signal of financial health

        **Factor 6 — Beta (5% weight)**
        Market sensitivity
        Balanced beta near 1.0 preferred

        **Factor 7 — Size (5% weight)**
        Market cap (smaller = higher score)
        Size premium (Fama & French 1992)
        """)

st.divider()

# ── Full Rankings Table ──────────────────────────────────────
st.subheader("📊 Full Factor Rankings")

# Filter options
col1, col2, col3 = st.columns(3)
with col1:
    market_filter = st.multiselect(
        "Market", ["ASX", "SP500"],
        default=["ASX", "SP500"]
    )
with col2:
    sector_filter = st.multiselect(
        "Sector",
        df["Sector"].unique().tolist(),
        default=df["Sector"].unique().tolist()
    )
with col3:
    min_score = st.slider("Min Composite Score", 0, 100, 0)

# Apply filters
filtered = df[
    (df["Market"].isin(market_filter)) &
    (df["Sector"].isin(sector_filter)) &
    (df["Composite"] >= min_score)
].copy()

st.dataframe(
    filtered[["Rank", "Ticker", "Name", "Sector",
              "Market", "Quality", "Value",
              "Technical", "Momentum", "Dividend",
              "Beta", "Composite"]],
    use_container_width=True,
    height=500
)

st.divider()

# ── Factor Heatmap ───────────────────────────────────────────
st.subheader("🌡️ Factor Score Heatmap")

factor_cols = ["Quality", "Value", "Technical",
               "Momentum", "Dividend", "Composite"]
heatmap_data = df.set_index("Ticker")[factor_cols]

fig = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,
    x=factor_cols,
    y=heatmap_data.index.tolist(),
    colorscale="RdYlGn",
    zmid=50,
    text=heatmap_data.values.round(1),
    texttemplate="%{text}",
    textfont={"size": 9},
    colorbar=dict(title="Score")
))

fig.update_layout(
    paper_bgcolor="#1a1a2e",
    plot_bgcolor="#1a1a2e",
    font_color="white",
    height=600,
    xaxis_title="Factor",
    yaxis_title="Stock"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Factor Charts ─────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top 10 by Composite Score")
    top10 = df.nlargest(10, "Composite")
    fig = px.bar(
        top10,
        x="Composite",
        y="Ticker",
        orientation="h",
        color="Composite",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100]
    )
    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font_color="white",
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📉 Factor Radar — Select Stock")
    selected = st.selectbox(
        "Stock", df["Ticker"].tolist()
    )
    row = df[df["Ticker"] == selected].iloc[0]

    categories = ["Quality", "Value", "Technical",
                  "Momentum", "Dividend"]
    values     = [row[c] for c in categories]
    values.append(values[0])  # close the radar
    categories.append(categories[0])

    fig = go.Figure(data=go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        line_color="cyan",
        fillcolor="rgba(0,255,255,0.2)"
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                color="white"
            ),
            bgcolor="#1a1a2e"
        ),
        paper_bgcolor="#1a1a2e",
        font_color="white",
        height=350,
        title=f"{selected} — Factor Radar"
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("AlgoTrade Pro — Factor Model")