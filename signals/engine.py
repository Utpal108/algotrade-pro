import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import ta
import warnings
from transformers import pipeline
warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════
# SIGNAL ENGINE — Combines all three analysis modules
# ════════════════════════════════════════════════════════════

ticker = "AAPL"
print(f"Running Signal Engine for {ticker}...")
print("=" * 50)

# ── SCORE 1: Technical Score ─────────────────────────────────
print("\n[1/3] Calculating Technical Score...")

df = pd.read_csv("data/AAPL_raw.csv", skiprows=[1, 2],
                 index_col=0, parse_dates=True)
df.columns = ["Close", "High", "Low", "Open", "Volume"]
df = df.dropna().sort_index()

# Calculate indicators
df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
macd      = ta.trend.MACD(df["Close"])
df["MACD"]        = macd.macd()
df["MACD_Signal"] = macd.macd_signal()
df["EMA_20"]  = ta.trend.EMAIndicator(df["Close"], window=20).ema_indicator()
df["EMA_50"]  = ta.trend.EMAIndicator(df["Close"], window=50).ema_indicator()
df["EMA_200"] = ta.trend.EMAIndicator(df["Close"], window=200).ema_indicator()

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
    (df["Close"].shift(1) <= df["Swing_High"].ffill().shift(1))
)
df["Bullish_OB"] = (
    (df["Close"].shift(1) < df["Open"].shift(1)) &
    (df["Close"] > df["Open"]) &
    (df["Close"] > df["Close"].shift(1) * 1.01)
)
df["FVG_Bullish"] = df["Low"] > df["High"].shift(2)

# Get latest values
latest       = df.iloc[-1]
rsi          = latest["RSI"]
macd_val     = latest["MACD"]
macd_sig     = latest["MACD_Signal"]
close        = latest["Close"]
ema20        = latest["EMA_20"]
ema50        = latest["EMA_50"]
ema200       = latest["EMA_200"]

# Score technical indicators 0-100
tech_score = 0

# RSI scoring
if 40 < rsi < 60:   tech_score += 20  # neutral zone
elif 30 < rsi < 70: tech_score += 15  # healthy range
elif rsi < 30:      tech_score += 25  # oversold = buy opportunity
else:               tech_score += 5   # overbought = caution

# MACD scoring
if macd_val > macd_sig: tech_score += 20  # bullish crossover
else:                   tech_score += 5   # bearish

# EMA trend scoring
if close > ema20 > ema50 > ema200: tech_score += 30  # perfect uptrend
elif close > ema50 > ema200:       tech_score += 20  # strong uptrend
elif close > ema200:               tech_score += 10  # above long term avg
else:                              tech_score += 0   # downtrend

# SMC scoring
recent = df.tail(20)
if recent["BOS_Bullish"].any():  tech_score += 15  # recent bullish BOS
if recent["Bullish_OB"].any():   tech_score += 10  # recent order block
if recent["FVG_Bullish"].any():  tech_score += 5   # recent FVG

tech_score = min(tech_score, 100)  # cap at 100

print(f"   RSI:               {rsi:.2f}")
print(f"   MACD vs Signal:    {macd_val:.3f} vs {macd_sig:.3f}")
print(f"   Price vs EMA200:   ${close:.2f} vs ${ema200:.2f}")
print(f"   Technical Score:   {tech_score}/100")

# ── SCORE 2: Fundamental Score ───────────────────────────────
print("\n[2/3] Calculating Fundamental Score...")

stock = yf.Ticker(ticker)
info  = stock.info

pe_ratio       = info.get("trailingPE", 0)
roe            = info.get("returnOnEquity", 0)
profit_margin  = info.get("profitMargins", 0)
debt_to_equity = info.get("debtToEquity", 0)
revenue_growth = info.get("revenueGrowth", 0)
current_price  = info.get("currentPrice", 0)

fund_score = 0

if pe_ratio < 15:        fund_score += 20
elif pe_ratio < 25:      fund_score += 15
elif pe_ratio < 35:      fund_score += 10
else:                    fund_score += 5

if roe > 0.20:           fund_score += 20
elif roe > 0.15:         fund_score += 15
elif roe > 0.10:         fund_score += 10
else:                    fund_score += 0

if profit_margin > 0.20: fund_score += 20
elif profit_margin > 0.10: fund_score += 15
elif profit_margin > 0.05: fund_score += 10
else:                    fund_score += 0

if debt_to_equity < 50:  fund_score += 20
elif debt_to_equity < 100: fund_score += 15
elif debt_to_equity < 200: fund_score += 10
else:                    fund_score += 0

if revenue_growth > 0.15:  fund_score += 20
elif revenue_growth > 0.08: fund_score += 15
elif revenue_growth > 0.03: fund_score += 10
else:                    fund_score += 0

print(f"   P/E Ratio:         {pe_ratio:.2f}")
print(f"   ROE:               {roe*100:.2f}%")
print(f"   Profit Margin:     {profit_margin*100:.2f}%")
print(f"   Fundamental Score: {fund_score}/100")

# ── SCORE 3: BERT Sentiment Score ────────────────────────────
print("\n[3/3] Calculating BERT Sentiment Score...")

finbert  = pipeline("text-classification",
                    model="ProsusAI/finbert",
                    tokenizer="ProsusAI/finbert")
news     = stock.news
headlines = []
for article in news[:20]:
    title = article.get("content", {}).get("title", "")
    if title:
        headlines.append(title)

positive = negative = neutral = 0
for headline in headlines:
    try:
        result = finbert(headline[:512])[0]
        if result["label"] == "positive":   positive += 1
        elif result["label"] == "negative": negative += 1
        else:                               neutral  += 1
    except:
        pass

total          = positive + negative + neutral
sentiment_score= (positive - negative) / total if total > 0 else 0
bert_score     = int((sentiment_score + 1) / 2 * 100)  # convert to 0-100

print(f"   Positive:          {positive}")
print(f"   Negative:          {negative}")
print(f"   Neutral:           {neutral}")
print(f"   BERT Score:        {bert_score}/100")

# ── COMPOSITE SIGNAL ─────────────────────────────────────────
# Weights: BERT 40%, Fundamental 30%, Technical 30%
# BERT weighted highest because sentiment drives short term price
weight_tech  = 0.30
weight_fund  = 0.30
weight_bert  = 0.40

composite_score = (
    tech_score  * weight_tech +
    fund_score  * weight_fund +
    bert_score  * weight_bert
)

print("\n" + "=" * 50)
print("COMPOSITE SIGNAL ENGINE RESULTS")
print("=" * 50)
print(f"Technical Score:    {tech_score}/100  (weight: 30%)")
print(f"Fundamental Score:  {fund_score}/100  (weight: 30%)")
print(f"BERT Score:         {bert_score}/100  (weight: 40%)")
print(f"Composite Score:    {composite_score:.1f}/100")

if composite_score >= 75:   final_signal = "🟢 STRONG BUY"
elif composite_score >= 60: final_signal = "🟡 BUY"
elif composite_score >= 40: final_signal = "⚪ HOLD"
elif composite_score >= 25: final_signal = "🟠 SELL"
else:                       final_signal = "🔴 STRONG SELL"

print(f"\nFINAL SIGNAL: {final_signal}")
print(f"Current Price: ${current_price:.2f}")
print("=" * 50)

# ── Chart ────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle(f"AAPL Signal Engine — Final Signal: {final_signal}", fontsize=13)

# Chart 1: Score breakdown bar chart
categories = ["Technical\n(30%)", "Fundamental\n(30%)", "BERT Sentiment\n(40%)"]
scores     = [tech_score, fund_score, bert_score]
colors     = ["cyan", "lime", "orange"]

bars = axes[0].bar(categories, scores, color=colors, alpha=0.8, width=0.4)
axes[0].axhline(75, color="lime", linestyle="--", linewidth=1, label="Strong Buy (75)")
axes[0].axhline(60, color="yellow", linestyle="--", linewidth=1, label="Buy (60)")
axes[0].axhline(40, color="orange", linestyle="--", linewidth=1, label="Hold (40)")
axes[0].set_ylim(0, 100)
axes[0].set_facecolor("#1a1a2e")
axes[0].set_ylabel("Score")
axes[0].set_title("Score Breakdown")
axes[0].legend(fontsize=8)
axes[0].grid(True, alpha=0.3)

for bar, score in zip(bars, scores):
    axes[0].text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + 1,
                 f"{score}", ha="center", fontsize=12,
                 color="white", fontweight="bold")

# Chart 2: Composite gauge
theta    = np.linspace(0, np.pi, 100)
axes[1].plot(np.cos(theta), np.sin(theta), "white", linewidth=2)
axes[1].fill_between(np.cos(theta[:33]),  np.sin(theta[:33]),  color="red",    alpha=0.3)
axes[1].fill_between(np.cos(theta[33:66]),np.sin(theta[33:66]),color="yellow", alpha=0.3)
axes[1].fill_between(np.cos(theta[66:]),  np.sin(theta[66:]),  color="lime",   alpha=0.3)

angle   = np.pi * (1 - composite_score / 100)
axes[1].annotate("", xy=(0.6*np.cos(angle), 0.6*np.sin(angle)),
                 xytext=(0, 0),
                 arrowprops=dict(arrowstyle="->", color="white", lw=2))
axes[1].text(0, -0.2, f"{composite_score:.1f}/100",
             ha="center", fontsize=16, color="white", fontweight="bold")
axes[1].text(0, -0.4, final_signal,
             ha="center", fontsize=12, color="yellow", fontweight="bold")
axes[1].text(-1, 0.1, "SELL",  fontsize=9, color="red")
axes[1].text(0.7, 0.1, "BUY",  fontsize=9, color="lime")
axes[1].text(-0.15, 0.95, "HOLD", fontsize=9, color="yellow")
axes[1].set_xlim(-1.2, 1.2)
axes[1].set_ylim(-0.6, 1.2)
axes[1].set_facecolor("#1a1a2e")
axes[1].set_title("Composite Signal Gauge")
axes[1].axis("off")

fig.patch.set_facecolor("#0f0f23")
plt.tight_layout()
plt.savefig("data/AAPL_signal_engine.png", dpi=150, bbox_inches="tight")
plt.show()
print("\n✅ Signal engine chart saved")