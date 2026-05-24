import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
from universe.stocks import ALL_TICKERS

st.set_page_config(
    page_title="Risk — AlgoTrade Pro",
    page_icon="⚠️",
    layout="wide"
)

st.title("⚠️ Risk Dashboard")
st.markdown("Portfolio risk metrics and analysis")
st.divider()

# ── Load Data ────────────────────────────────────────────────
try:
    risk    = pd.read_csv("data/risk_metrics.csv")
    port    = pd.read_csv("data/portfolio.csv")
except:
    st.error("Run portfolio/risk.py first")
    st.stop()

# ── Risk KPIs ─────────────────────────────────────────────────
st.subheader("📊 Risk Metrics")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Daily VaR 95%",
            f"{risk['var_95_pct'].iloc[0]:.2f}%",
            f"${risk['var_95_dollar'].iloc[0]:,.0f}")
col2.metric("Daily VaR 99%",
            f"{risk['var_99_pct'].iloc[0]:.2f}%",
            f"${risk['var_99_dollar'].iloc[0]:,.0f}")
col3.metric("CVaR 95%",
            f"{risk['cvar_95_pct'].iloc[0]:.2f}%",
            f"${risk['cvar_95_dollar'].iloc[0]:,.0f}")
col4.metric("Max Drawdown",
            f"{risk['max_drawdown'].iloc[0]:.2f}%")
col5.metric("Total Return",
            f"{risk['total_return'].iloc[0]:.1f}%")

st.divider()

# ── VaR Explanation ───────────────────────────────────────────
with st.expander("📚 Understanding Value at Risk (VaR)"):
    st.markdown("""
    **VaR 95%** means: On 95% of trading days,
    your portfolio will NOT lose more than this amount.
    Only 1 in 20 days will be worse.

    **VaR 99%** means: On 99% of trading days,
    your portfolio will NOT lose more than this amount.
    Only 1 in 100 days will be worse.

    **CVaR (Conditional VaR)** means: On the days when
    losses DO exceed VaR, the average loss will be
    this amount. Also called Expected Shortfall.

    **Max Drawdown** is the largest peak-to-trough
    decline in portfolio value. It measures the worst
    case scenario that actually happened historically.
    """)

st.divider()

# ── Load price data for charts ────────────────────────────────
@st.cache_data
def load_returns():
    returns_dict  = {}
    weights_dict  = {}
    for _, row in port.iterrows():
        ticker = row["Ticker"]
        weight = row["Weight"] / 100
        path   = f"data/prices/{ticker.replace('.','_')}.csv"
        try:
            df = pd.read_csv(path, index_col=0,
                             parse_dates=True)
            df.columns = ["Close", "High", "Low",
                          "Open", "Volume"]
            returns_dict[ticker] = df["Close"].pct_change(
            ).dropna()
            weights_dict[ticker] = weight
        except:
            pass
    returns_df    = pd.DataFrame(returns_dict).dropna()
    weights_array = np.array([
        weights_dict.get(t, 0)
        for t in returns_df.columns
    ])
    weights_array = weights_array / weights_array.sum()
    port_returns  = returns_df.dot(weights_array)
    return port_returns, returns_df

port_returns, returns_df = load_returns()
capital          = 100000
portfolio_values = capital * (1 + port_returns).cumprod()

# ── Charts ────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Portfolio Value")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=portfolio_values.index,
        y=portfolio_values.values,
        fill="tozeroy",
        fillcolor="rgba(0,255,136,0.15)",
        line=dict(color="#00ff88", width=1.5),
        name="Portfolio Value"
    ))
    fig.add_hline(y=capital,
                  line_dash="dash",
                  line_color="white",
                  annotation_text="Starting Capital")
    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font_color="white",
        height=350,
        yaxis_title="Value ($)"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📊 Return Distribution")
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=port_returns * 100,
        nbinsx=50,
        marker_color="cyan",
        opacity=0.7,
        name="Daily Returns"
    ))
    var95 = np.percentile(port_returns, 5) * 100
    var99 = np.percentile(port_returns, 1) * 100
    fig.add_vline(x=var95,
                  line_dash="dash",
                  line_color="orange",
                  annotation_text=f"VaR 95%: {var95:.2f}%")
    fig.add_vline(x=var99,
                  line_dash="dash",
                  line_color="red",
                  annotation_text=f"VaR 99%: {var99:.2f}%")
    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font_color="white",
        height=350,
        xaxis_title="Daily Return (%)"
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Drawdown Chart ────────────────────────────────────────────
st.subheader("📉 Drawdown Analysis")
rolling_max = portfolio_values.cummax()
drawdown    = (portfolio_values - rolling_max) / rolling_max * 100

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=drawdown.index,
    y=drawdown.values,
    fill="tozeroy",
    fillcolor="rgba(255,68,68,0.3)",
    line=dict(color="#ff4444", width=1),
    name="Drawdown"
))
fig.update_layout(
    paper_bgcolor="#1a1a2e",
    plot_bgcolor="#1a1a2e",
    font_color="white",
    height=300,
    yaxis_title="Drawdown (%)"
)
st.plotly_chart(fig, use_container_width=True)

# ── Correlation Heatmap ───────────────────────────────────────
st.subheader("🔗 Correlation Matrix")
st.markdown("Green = low correlation (good diversification) "
            "| Yellow/Red = high correlation (concentration risk)")

corr_matrix   = returns_df.corr()
tickers_short = [t.replace(".AX", "") for t in corr_matrix.columns]

fig = go.Figure(data=go.Heatmap(
    z=corr_matrix.values,
    x=tickers_short,
    y=tickers_short,
    colorscale="RdYlGn",
    zmid=0,
    zmin=-1,
    zmax=1,
    text=corr_matrix.values.round(2),
    texttemplate="%{text}",
    textfont={"size": 8},
    colorbar=dict(title="Correlation")
))
fig.update_layout(
    paper_bgcolor="#1a1a2e",
    plot_bgcolor="#1a1a2e",
    font_color="white",
    height=550
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("AlgoTrade Pro — Risk Dashboard")