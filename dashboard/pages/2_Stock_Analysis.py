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
    ticker = st.selectbox(
        "Select Stock",
        ALL_TICKERS,
        index=0
    )
    analyze = st.button("🚀 Analyze", type="primary")

with col2:
    if ticker in ALL_STOCKS:
        info = ALL_STOCKS[ticker]
        st.markdown(f"### {info['name']}")
        st.markdown(f"**Sector:** {info['sector']} | "
                    f"**Market:** {info['market']} | "
                    f"**Currency:** {info['currency']}")

st.divider()

if analyze or True:  # auto load on selection
    # ── Load Data ────────────────────────────────────────────
    with st.spinner(f"Loading {ticker}..."):
        path = f"data/prices/{ticker.replace('.', '_')}.csv"
        try:
            df = pd.read_csv(path, index_col=0,
                             parse_dates=True)
            df.columns = ["Close", "High", "Low",
                          "Open", "Volume"]
            df = df.dropna().sort_index()
        except:
            st.error(f"No data for {ticker}. "
                     f"Run fetch_data.py first")
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

    # ── Key Metrics ──────────────────────────────────────────
    latest = df.iloc[-1]
    prev   = df.iloc[-2]
    change = (latest["Close"] - prev["Close"]) / \
              prev["Close"] * 100

    col1, col2, col3, col4, col5 = st.columns(5)
    currency = ALL_STOCKS[ticker]["currency"]
    symbol   = "A$" if currency == "AUD" else "$"

    col1.metric("Price",
                f"{symbol}{latest['Close']:.2f}",
                f"{change:.2f}%")
    col2.metric("RSI",
                f"{latest['RSI']:.1f}",
                "Overbought" if latest["RSI"] > 70
                else "Oversold" if latest["RSI"] < 30
                else "Neutral")
    col3.metric("EMA 200",
                f"{symbol}{latest['EMA_200']:.2f}",
                "Above ✅" if latest["Close"] > latest["EMA_200"]
                else "Below ⚠️")
    col4.metric("52W High",
                f"{symbol}{df['High'].tail(252).max():.2f}")
    col5.metric("52W Low",
                f"{symbol}{df['Low'].tail(252).min():.2f}")

    st.divider()

    # ── Candlestick Chart ────────────────────────────────────
    st.subheader("📈 Price Chart")

    # Date range selector
    period = st.radio("Period",
                      ["1Y", "2Y", "5Y"],
                      horizontal=True)
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
        increasing_line_color="#00ff88",
        decreasing_line_color="#ff4444"
    ))

    # EMAs
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df["EMA_20"],
        name="EMA 20", line=dict(color="yellow", width=1)
    ))
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df["EMA_50"],
        name="EMA 50", line=dict(color="orange", width=1)
    ))
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df["EMA_200"],
        name="EMA 200", line=dict(color="red", width=1)
    ))

    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df["BB_Upper"],
        name="BB Upper",
        line=dict(color="cyan", width=0.5, dash="dash")
    ))
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df["BB_Lower"],
        name="BB Lower",
        line=dict(color="cyan", width=0.5, dash="dash"),
        fill="tonexty", fillcolor="rgba(0,255,255,0.05)"
    ))

    # Swing Highs
    swing_high_df = plot_df.dropna(subset=["Swing_High"])
    fig.add_trace(go.Scatter(
        x=swing_high_df.index,
        y=swing_high_df["Swing_High"],
        mode="markers",
        name="Swing High",
        marker=dict(color="lime", symbol="triangle-up", size=8)
    ))

    # Swing Lows
    swing_low_df = plot_df.dropna(subset=["Swing_Low"])
    fig.add_trace(go.Scatter(
        x=swing_low_df.index,
        y=swing_low_df["Swing_Low"],
        mode="markers",
        name="Swing Low",
        marker=dict(color="red", symbol="triangle-down", size=8)
    ))

    # BOS signals
    bos_df = plot_df[plot_df["BOS_Bullish"]]
    fig.add_trace(go.Scatter(
        x=bos_df.index,
        y=bos_df["Close"],
        mode="markers",
        name="BOS Bullish",
        marker=dict(color="cyan", symbol="star", size=12)
    ))

    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font_color="white",
        xaxis_rangeslider_visible=False,
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── RSI + MACD ───────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("RSI")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(
            x=plot_df.index, y=plot_df["RSI"],
            name="RSI", line=dict(color="yellow", width=1.5)
        ))
        fig_rsi.add_hline(y=70, line_dash="dash",
                          line_color="red",
                          annotation_text="Overbought")
        fig_rsi.add_hline(y=30, line_dash="dash",
                          line_color="lime",
                          annotation_text="Oversold")
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
            name="MACD", line=dict(color="cyan", width=1.5)
        ))
        fig_macd.add_trace(go.Scatter(
            x=plot_df.index, y=plot_df["MACD_Signal"],
            name="Signal", line=dict(color="orange", width=1.5)
        ))
        colors = ["lime" if v >= 0 else "red"
                  for v in plot_df["MACD_Hist"]]
        fig_macd.add_trace(go.Bar(
            x=plot_df.index, y=plot_df["MACD_Hist"],
            name="Histogram", marker_color=colors
        ))
        fig_macd.update_layout(
            paper_bgcolor="#1a1a2e",
            plot_bgcolor="#1a1a2e",
            font_color="white",
            height=250
        )
        st.plotly_chart(fig_macd, use_container_width=True)

    st.divider()

    # ── Factor Score ─────────────────────────────────────────
    st.subheader("🔢 Factor Score")
    try:
        factor_scores = pd.read_csv("data/factor_scores.csv")
        row = factor_scores[
            factor_scores["Ticker"] == ticker].iloc[0]

        col1, col2, col3, col4, col5, col6, col7 = \
            st.columns(7)
        col1.metric("Quality",   f"{row['Quality']:.0f}")
        col2.metric("Value",     f"{row['Value']:.0f}")
        col3.metric("Technical", f"{row['Technical']:.0f}")
        col4.metric("Momentum",  f"{row['Momentum']:.0f}")
        col5.metric("Dividend",  f"{row['Dividend']:.0f}")
        col6.metric("Beta",      f"{row['Beta']:.2f}")
        col7.metric("Composite", f"{row['Composite']:.1f}")

        composite = row["Composite"]
        if composite >= 75:
            st.success(f"## 🟢 STRONG BUY — Score: {composite:.1f}/100")
        elif composite >= 60:
            st.success(f"## 🟡 BUY — Score: {composite:.1f}/100")
        elif composite >= 40:
            st.warning(f"## ⚪ HOLD — Score: {composite:.1f}/100")
        else:
            st.error(f"## 🔴 SELL — Score: {composite:.1f}/100")
    except:
        st.warning("Run analysis/factors.py first")

st.divider()
# ── BERT Sentiment ───────────────────────────────────────────
st.subheader("🤖 BERT Sentiment Analysis")

col1, col2 = st.columns(2)

with col1:
    # Load saved BERT scores
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

        # Score metrics
        col1a, col1b, col1c, col1d = st.columns(4)
        col1a.metric("BERT Score",  f"{bert_score}/100")
        col1b.metric("Positive",    positive)
        col1c.metric("Negative",    negative)
        col1d.metric("Neutral",     neutral)

        # Signal
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
    # Live BERT button
    st.markdown("### Run Live BERT Analysis")
    st.markdown("Analyzes latest headlines right now")

    if st.button("🤖 Run Live BERT", type="primary"):
        with st.spinner("Loading FinBERT and analyzing..."):
            from transformers import pipeline
            import yfinance as yf

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
            score = int(((pos-neg)/total + 1)/2*100) \
                    if total > 0 else 50

            st.metric("Live BERT Score", f"{score}/100")
            st.dataframe(pd.DataFrame(results),
                         use_container_width=True)
st.caption("AlgoTrade Pro — Stock Analysis")