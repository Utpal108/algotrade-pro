import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
import ta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
from universe.stocks import ALL_STOCKS, ALL_TICKERS

st.set_page_config(
    page_title="Stock Analysis — AlgoTrade Pro",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Stock Analysis")
st.markdown("Deep dive into any stock in our universe")
st.divider()

# ── Stock Selector ───────────────────────────────────────────
col1, col2 = st.columns([1, 3])

with col1:
    ticker = st.selectbox("Select Stock", ALL_TICKERS, index=0)

with col2:
    if ticker in ALL_STOCKS:
        info = ALL_STOCKS[ticker]
        st.markdown(f"### {info['name']}")
        st.markdown(
            f"**Sector:** {info['sector']} | "
            f"**Market:** {info['market']} | "
            f"**Currency:** {info['currency']}"
        )

st.divider()

# ── Load Price Data ──────────────────────────────────────────
with st.spinner(f"Loading {ticker}..."):
    path = f"data/prices/{ticker.replace('.', '_')}.csv"
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.columns = ["Close", "High", "Low", "Open", "Volume"]
        df = df.dropna().sort_index()
    except:
        st.error(f"No data for {ticker}. Run fetch_data.py first")
        st.stop()

    # Calculate indicators
    df["RSI"] = ta.momentum.RSIIndicator(
        df["Close"], window=14).rsi()
    macd = ta.trend.MACD(df["Close"])
    df["MACD"]        = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    df["MACD_Hist"]   = macd.macd_diff()
    bb = ta.volatility.BollingerBands(df["Close"], window=20)
    df["BB_Upper"] = bb.bollinger_hband()
    df["BB_Lower"] = bb.bollinger_lband()
    df["EMA_20"]   = ta.trend.EMAIndicator(
        df["Close"], window=20).ema_indicator()
    df["EMA_50"]   = ta.trend.EMAIndicator(
        df["Close"], window=50).ema_indicator()
    df["EMA_200"]  = ta.trend.EMAIndicator(
        df["Close"], window=200).ema_indicator()

    # SMC
    df["Swing_High"] = df["High"][
        (df["High"] > df["High"].shift(1)) &
        (df["High"] > df["High"].shift(-1))
    ]
    df["Swing_Low"] = df["Low"][
        (df["Low"] < df["Low"].shift(1)) &
        (df["Low"] < df["Low"].shift(-1))
    ]
    df["BOS_Bullish"] = (
        (df["Close"] > df["Swing_High"].ffill()) &
        (df["Close"].shift(1) <=
         df["Swing_High"].ffill().shift(1))
    )

# ── Live Price ───────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_live_price_cached(ticker):
    try:
        live_df = pd.read_csv("data/live_prices.csv")
        row = live_df[live_df["ticker"] == ticker]
        if not row.empty:
            return row.iloc[0]
    except:
        pass
    return None

live_row      = get_live_price_cached(ticker)
latest        = df.iloc[-1]
prev          = df.iloc[-2]
currency      = ALL_STOCKS[ticker]["currency"]
symbol        = "A$" if currency == "AUD" else "$"

if live_row is not None:
    current_price = live_row["price"]
    change_pct    = live_row["change_pct"]
    day_high      = live_row["day_high"]
    day_low       = live_row["day_low"]
    is_live       = True
else:
    current_price = latest["Close"]
    change_pct    = (latest["Close"] - prev["Close"]) / \
                     prev["Close"] * 100
    day_high      = latest["High"]
    day_low       = latest["Low"]
    is_live       = False

if is_live:
    st.success("📡 Live price data active")
else:
    st.info("📊 Showing historical close price")

# ── Key Metrics ──────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(
    "Live Price" if is_live else "Last Close",
    f"{symbol}{current_price:.2f}",
    f"{change_pct:+.2f}%"
)
col2.metric(
    "RSI", f"{latest['RSI']:.1f}",
    "Overbought" if latest["RSI"] > 70
    else "Oversold" if latest["RSI"] < 30
    else "Neutral"
)
col3.metric(
    "EMA 200",
    f"{symbol}{latest['EMA_200']:.2f}",
    "Above ✅" if current_price > latest["EMA_200"]
    else "Below ⚠️"
)
col4.metric("Day High", f"{symbol}{day_high:.2f}")
col5.metric("Day Low",  f"{symbol}{day_low:.2f}")

st.divider()

# ── Price Chart ──────────────────────────────────────────────
st.subheader("📈 Price Chart")

period = st.radio("Period", ["1Y", "2Y", "5Y"], horizontal=True)
days   = {"1Y": 252, "2Y": 504, "5Y": 1260}
plot_df = df.tail(days[period])

fig = go.Figure()

# Candlesticks
fig.add_trace(go.Candlestick(
    x=plot_df.index,
    open=plot_df["Open"],
    high=plot_df["High"],
    low=plot_df["Low"],
    close=plot_df["Close"],
    name="Price",
    increasing=dict(
        line=dict(color="#00ff88", width=1),
        fillcolor="#00ff88"
    ),
    decreasing=dict(
        line=dict(color="#ff4444", width=1),
        fillcolor="#ff4444"
    )
))

# EMAs
fig.add_trace(go.Scatter(
    x=plot_df.index, y=plot_df["EMA_50"],
    name="EMA 50",
    line=dict(color="#ffaa00", width=1.5),
    opacity=0.8
))
fig.add_trace(go.Scatter(
    x=plot_df.index, y=plot_df["EMA_200"],
    name="EMA 200",
    line=dict(color="#ff4444", width=2.0),
    opacity=0.9
))

# Bollinger Bands
fig.add_trace(go.Scatter(
    x=plot_df.index, y=plot_df["BB_Upper"],
    name="BB Upper",
    line=dict(color="rgba(0,200,255,0.3)", width=1),
    showlegend=False
))
fig.add_trace(go.Scatter(
    x=plot_df.index, y=plot_df["BB_Lower"],
    name="BB Band",
    line=dict(color="rgba(0,200,255,0.3)", width=1),
    fill="tonexty",
    fillcolor="rgba(0,200,255,0.03)"
))

# SMC — last 60 days only
recent_cutoff = plot_df.index[-60] if len(plot_df) > 60 \
                else plot_df.index[0]
swing_high_recent = plot_df.dropna(
    subset=["Swing_High"])[
    plot_df.dropna(subset=["Swing_High"]).index >= recent_cutoff
]
swing_low_recent = plot_df.dropna(
    subset=["Swing_Low"])[
    plot_df.dropna(subset=["Swing_Low"]).index >= recent_cutoff
]

fig.add_trace(go.Scatter(
    x=swing_high_recent.index,
    y=swing_high_recent["Swing_High"],
    mode="markers",
    name="Swing High",
    marker=dict(
        color="rgba(0,255,136,0.7)",
        symbol="triangle-up",
        size=10,
        line=dict(color="white", width=1)
    )
))
fig.add_trace(go.Scatter(
    x=swing_low_recent.index,
    y=swing_low_recent["Swing_Low"],
    mode="markers",
    name="Swing Low",
    marker=dict(
        color="rgba(255,68,68,0.7)",
        symbol="triangle-down",
        size=10,
        line=dict(color="white", width=1)
    )
))

# BOS — last 3 only
bos_df = plot_df[plot_df["BOS_Bullish"]].tail(3)
if not bos_df.empty:
    fig.add_trace(go.Scatter(
        x=bos_df.index,
        y=bos_df["Close"] * 0.985,
        mode="markers+text",
        name="BOS",
        text=["BOS"] * len(bos_df),
        textposition="bottom center",
        textfont=dict(color="cyan", size=9),
        marker=dict(
            color="cyan",
            symbol="star",
            size=14,
            line=dict(color="white", width=1)
        )
    ))

# Volume
colors_vol = [
    "#00ff88" if plot_df["Close"].iloc[i] >=
    plot_df["Open"].iloc[i] else "#ff4444"
    for i in range(len(plot_df))
]
fig.add_trace(go.Bar(
    x=plot_df.index,
    y=plot_df["Volume"],
    name="Volume",
    marker_color=colors_vol,
    opacity=0.4,
    yaxis="y2"
))

# Layout
fig.update_layout(
    paper_bgcolor="#0f0f23",
    plot_bgcolor="#1a1a2e",
    font=dict(color="white", size=11),
    xaxis=dict(
        rangeslider=dict(visible=False),
        gridcolor="rgba(255,255,255,0.05)",
        showgrid=True
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        showgrid=True,
        side="right",
        title="Price"
    ),
    yaxis2=dict(
        overlaying="y",
        side="left",
        showgrid=False,
        showticklabels=False,
        range=[0, plot_df["Volume"].max() * 5]
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        bgcolor="rgba(0,0,0,0.3)",
        bordercolor="rgba(255,255,255,0.1)",
        borderwidth=1
    ),
    height=550,
    margin=dict(l=10, r=60, t=60, b=10),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# ── RSI + MACD ───────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("RSI")
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df["RSI"],
        name="RSI",
        line=dict(color="yellow", width=1.5)
    ))
    fig_rsi.add_hline(
        y=70, line_dash="dash", line_color="red",
        annotation_text="Overbought"
    )
    fig_rsi.add_hline(
        y=30, line_dash="dash", line_color="lime",
        annotation_text="Oversold"
    )
    fig_rsi.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font_color="white",
        yaxis=dict(range=[0, 100]),
        height=250
    )
    st.plotly_chart(fig_rsi, use_container_width=True)

with col2:
    st.subheader("MACD")
    fig_macd = go.Figure()
    fig_macd.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df["MACD"],
        name="MACD",
        line=dict(color="cyan", width=1.5)
    ))
    fig_macd.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df["MACD_Signal"],
        name="Signal",
        line=dict(color="orange", width=1.5)
    ))
    colors = ["lime" if v >= 0 else "red"
              for v in plot_df["MACD_Hist"]]
    fig_macd.add_trace(go.Bar(
        x=plot_df.index,
        y=plot_df["MACD_Hist"],
        name="Histogram",
        marker_color=colors
    ))
    fig_macd.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font_color="white",
        height=250
    )
    st.plotly_chart(fig_macd, use_container_width=True)

st.divider()

# ── Factor Score ─────────────────────────────────────────────
st.subheader("🔢 Factor Score")
try:
    factor_scores = pd.read_csv("data/factor_scores.csv")
    row = factor_scores[
        factor_scores["Ticker"] == ticker].iloc[0]

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    col1.metric("Quality",   f"{row['Quality']:.0f}")
    col2.metric("Value",     f"{row['Value']:.0f}")
    col3.metric("Technical", f"{row['Technical']:.0f}")
    col4.metric("Momentum",  f"{row['Momentum']:.0f}")
    col5.metric("Dividend",  f"{row['Dividend']:.0f}")
    col6.metric("Beta",      f"{row['Beta']:.2f}")
    col7.metric("Composite", f"{row['Composite']:.1f}")

    composite = row["Composite"]
    if composite >= 75:
        st.success(
            f"## 🟢 STRONG BUY — Score: {composite:.1f}/100")
    elif composite >= 60:
        st.success(
            f"## 🟡 BUY — Score: {composite:.1f}/100")
    elif composite >= 40:
        st.warning(
            f"## ⚪ HOLD — Score: {composite:.1f}/100")
    else:
        st.error(
            f"## 🔴 SELL — Score: {composite:.1f}/100")
except:
    st.warning("Run analysis/factors.py first")

st.divider()

# ── BERT Sentiment ───────────────────────────────────────────
st.subheader("🤖 BERT Sentiment")

col1, col2 = st.columns(2)

with col1:
    try:
        bert_df  = pd.read_csv("data/bert_scores.csv")
        bert_row = bert_df[
            bert_df["ticker"] == ticker].iloc[0]

        bert_score = bert_row["bert_score"]
        signal     = bert_row["signal"]
        positive   = bert_row["positive"]
        negative   = bert_row["negative"]
        neutral    = bert_row["neutral"]
        headline   = bert_row["top_headline"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("BERT Score", f"{bert_score}/100")
        c2.metric("Positive",   positive)
        c3.metric("Negative",   negative)
        c4.metric("Neutral",    neutral)

        if bert_score >= 60:
            st.success(f"🟢 {signal}")
        elif bert_score >= 40:
            st.warning(f"⚪ {signal}")
        else:
            st.error(f"🔴 {signal}")

        st.markdown(f"**Top headline:** {headline}")

    except:
        st.warning("Run analysis/bert_batch.py first")

with col2:
    st.markdown("### Run Live BERT")
    st.markdown("Analyzes latest headlines right now")
    if st.button("🤖 Run Live BERT", type="primary"):
        with st.spinner("Analyzing headlines..."):
            from transformers import pipeline
            finbert = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert"
            )
            stock     = yf.Ticker(ticker)
            news      = stock.news
            headlines = []
            results   = []
            for article in news[:15]:
                title = article.get(
                    "content", {}).get("title", "")
                if title:
                    headlines.append(title)

            pos = neg = neu = 0
            for h in headlines:
                try:
                    r = finbert(h[:512])[0]
                    if r["label"] == "positive":   pos += 1
                    elif r["label"] == "negative": neg += 1
                    else:                          neu += 1
                    results.append({
                        "Headline":   h[:60],
                        "Sentiment":  r["label"],
                        "Confidence": f"{r['score']:.2f}"
                    })
                except:
                    pass

            total = pos + neg + neu
            score = int(((pos - neg) / total + 1) / 2 * 100) \
                    if total > 0 else 50
            st.metric("Live BERT Score", f"{score}/100")
            if results:
                st.dataframe(
                    pd.DataFrame(results),
                    use_container_width=True
                )

st.divider()
st.caption("AlgoTrade Pro — Stock Analysis")