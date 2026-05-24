import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
from universe.stocks import ALL_STOCKS

st.set_page_config(
    page_title="Execution — AlgoTrade Pro",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Execution Center")
st.markdown("Trade signals, position sizing, and order management")
st.divider()

# ── Load Data ─────────────────────────────────────────────────
try:
    portfolio     = pd.read_csv("data/portfolio.csv")
    factor_scores = pd.read_csv("data/factor_scores.csv")
except:
    st.error("Run optimizer and factor model first")
    st.stop()

# ── Signal Summary ────────────────────────────────────────────
st.subheader("🎯 Current Signals")

# Generate signals from factor scores
signals = []
for _, row in factor_scores.iterrows():
    score = row["Composite"]
    if score >= 75:
        signal    = "🟢 STRONG BUY"
        action    = "BUY"
        priority  = 1
    elif score >= 65:
        signal    = "🟡 BUY"
        action    = "BUY"
        priority  = 2
    elif score >= 50:
        signal    = "⚪ HOLD"
        action    = "HOLD"
        priority  = 3
    elif score >= 35:
        signal    = "🟠 REDUCE"
        action    = "SELL"
        priority  = 4
    else:
        signal    = "🔴 SELL"
        action    = "SELL"
        priority  = 5

    signals.append({
        "Ticker":    row["Ticker"],
        "Name":      row["Name"],
        "Sector":    row["Sector"],
        "Score":     score,
        "Signal":    signal,
        "Action":    action,
        "Priority":  priority
    })

signals_df = pd.DataFrame(signals).sort_values("Priority")

# Signal counts
col1, col2, col3, col4 = st.columns(4)
buy_count  = len(signals_df[signals_df["Action"] == "BUY"])
hold_count = len(signals_df[signals_df["Action"] == "HOLD"])
sell_count = len(signals_df[signals_df["Action"] == "SELL"])

col1.metric("🟢 Buy Signals",  buy_count)
col2.metric("⚪ Hold Signals", hold_count)
col3.metric("🔴 Sell Signals", sell_count)
col4.metric("Total Stocks",    len(signals_df))

st.divider()

# ── Signal Table ──────────────────────────────────────────────
st.subheader("📋 All Signals")

action_filter = st.multiselect(
    "Filter by Action",
    ["BUY", "HOLD", "SELL"],
    default=["BUY", "HOLD", "SELL"]
)

filtered_signals = signals_df[
    signals_df["Action"].isin(action_filter)
]

st.dataframe(
    filtered_signals[["Ticker", "Name", "Sector",
                       "Score", "Signal"]],
    use_container_width=True,
    height=400
)
# ── BERT Sentiment Overview ───────────────────────────────────
st.subheader("🤖 BERT Sentiment Scores")

try:
    bert_df = pd.read_csv("data/bert_scores.csv")
    bert_df.columns = bert_df.columns.str.strip()
    bert_df = bert_df.rename(columns={"ticker": "Ticker"})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Most Positive Sentiment:**")
        top3 = bert_df.nlargest(3, "bert_score")
        for _, row in top3.iterrows():
            st.success(f"🟢 {row['Ticker']} — "
                      f"{row['bert_score']}/100 "
                      f"— {row['signal']}")

    with col2:
        st.markdown("**Most Negative Sentiment:**")
        bot3 = bert_df.nsmallest(3, "bert_score")
        for _, row in bot3.iterrows():
            st.error(f"🔴 {row['Ticker']} — "
                    f"{row['bert_score']}/100 "
                    f"— {row['signal']}")

    st.divider()

    st.markdown("**All BERT Scores:**")
    bert_display = bert_df[[
        "Ticker", "bert_score", "signal",
        "positive", "negative", "neutral",
        "top_headline"
    ]].sort_values("bert_score", ascending=False)

    st.dataframe(bert_display,
                 use_container_width=True,
                 height=300)

except Exception as e:
    st.error(f"BERT error: {e}")

    # Merge with signals
    merged = signals_df.merge(
        bert_df[["Ticker", "bert_score", "signal",
                 "top_headline"]],
        on="Ticker", how="left"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Most Positive Sentiment:**")
        top3 = bert_df.nlargest(3, "bert_score")
        for _, row in top3.iterrows():
            st.success(f"🟢 {row['ticker']} — "
                      f"{row['bert_score']}/100 "
                      f"— {row['signal']}")

    with col2:
        st.markdown("**Most Negative Sentiment:**")
        bot3 = bert_df.nsmallest(3, "bert_score")
        for _, row in bot3.iterrows():
            st.error(f"🔴 {row['ticker']} — "
                    f"{row['bert_score']}/100 "
                    f"— {row['signal']}")

    st.divider()

    # Full BERT table
    st.markdown("**All BERT Scores:**")
    bert_display = bert_df[[
        "ticker", "bert_score", "signal",
        "positive", "negative", "neutral",
        "top_headline"
    ]].sort_values("bert_score", ascending=False)

    st.dataframe(bert_display,
                 use_container_width=True,
                 height=300)

except:
    st.warning("Run analysis/bert_batch.py first")

st.divider()

# ── Position Sizing Calculator ────────────────────────────────
st.subheader("🧮 Position Sizing Calculator")
st.markdown("""
Position sizing determines how much capital to allocate
to each trade. We use the **Kelly Criterion** as a guide
but cap at portfolio rules.
""")

col1, col2 = st.columns(2)

with col1:
    calc_capital   = st.number_input(
        "Portfolio Capital ($)",
        min_value=1000,
        max_value=10000000,
        value=100000,
        step=1000
    )
    calc_ticker    = st.selectbox(
        "Select Stock",
        signals_df["Ticker"].tolist()
    )
    calc_risk      = st.slider(
        "Risk per trade (%)",
        min_value=0.5,
        max_value=5.0,
        value=2.0,
        step=0.5
    )
    stop_loss      = st.slider(
        "Stop Loss (%)",
        min_value=2,
        max_value=15,
        value=8,
        step=1
    )

with col2:
    # Position sizing formula
    # Position Size = (Capital × Risk%) / Stop Loss%
    risk_amount    = calc_capital * (calc_risk / 100)
    position_size  = risk_amount / (stop_loss / 100)
    max_position   = calc_capital * 0.15

    final_position = min(position_size, max_position)
    pct_of_port    = final_position / calc_capital * 100

    st.markdown("### Position Size Result")
    st.metric("Risk Amount",
              f"${risk_amount:,.0f}",
              f"{calc_risk}% of capital")
    st.metric("Calculated Position",
              f"${position_size:,.0f}")
    st.metric("Max Allowed (15%)",
              f"${max_position:,.0f}")
    st.metric("Final Position Size",
              f"${final_position:,.0f}",
              f"{pct_of_port:.1f}% of portfolio")

    if position_size > max_position:
        st.warning("⚠️ Position capped at 15% portfolio limit")
    else:
        st.success("✅ Position within risk limits")

st.divider()

# ── Rebalancing Orders ─────────────────────────────────────────
st.subheader("🔄 Rebalancing Orders")
st.markdown("Based on current optimal weights vs equal weight")

rebalance_orders = []
equal_weight     = 100 / len(portfolio)

for _, row in portfolio.iterrows():
    current_weight = row["Weight"]
    target_weight  = equal_weight
    drift          = current_weight - target_weight

    if abs(drift) > 2:  # only rebalance if drift > 2%
        action = "REDUCE" if drift > 0 else "INCREASE"
        rebalance_orders.append({
            "Ticker":         row["Ticker"],
            "Name":           row["Name"],
            "Current Weight": f"{current_weight:.1f}%",
            "Target Weight":  f"{target_weight:.1f}%",
            "Drift":          f"{drift:+.1f}%",
            "Action":         action
        })

if rebalance_orders:
    st.dataframe(
        pd.DataFrame(rebalance_orders),
        use_container_width=True
    )
else:
    st.success("✅ Portfolio is within rebalancing thresholds")

st.divider()

# ── Signal Chart ──────────────────────────────────────────────
st.subheader("📊 Signal Distribution")
fig = px.bar(
    signals_df.sort_values("Score", ascending=True),
    x="Score",
    y="Ticker",
    orientation="h",
    color="Score",
    color_continuous_scale="RdYlGn",
    range_color=[0, 100],
    title="Factor Scores — All 20 Stocks"
)
fig.update_layout(
    paper_bgcolor="#1a1a2e",
    plot_bgcolor="#1a1a2e",
    font_color="white",
    height=550
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("AlgoTrade Pro — Execution Center")