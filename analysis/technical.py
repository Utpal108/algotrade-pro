import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ta

# ── Load price data ──────────────────────────────────────────
df = pd.read_csv("data/AAPL_raw.csv", skiprows=[1, 2], index_col=0, parse_dates=True)
df.columns = ["Close", "High", "Low", "Open", "Volume"]
df = df.dropna()
df = df.sort_index()
print("✅ Data loaded")

# ── Classic Indicators ───────────────────────────────────────
df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()

macd = ta.trend.MACD(df["Close"])
df["MACD"]        = macd.macd()
df["MACD_Signal"] = macd.macd_signal()
df["MACD_Hist"]   = macd.macd_diff()

bb = ta.volatility.BollingerBands(df["Close"], window=20)
df["BB_Upper"] = bb.bollinger_hband()
df["BB_Lower"] = bb.bollinger_lband()
df["BB_Mid"]   = bb.bollinger_mavg()

df["VWAP"] = ta.volume.VolumeWeightedAveragePrice(
    df["High"], df["Low"], df["Close"], df["Volume"]
).volume_weighted_average_price()

df["EMA_20"]  = ta.trend.EMAIndicator(df["Close"], window=20).ema_indicator()
df["EMA_50"]  = ta.trend.EMAIndicator(df["Close"], window=50).ema_indicator()
df["EMA_200"] = ta.trend.EMAIndicator(df["Close"], window=200).ema_indicator()

print("✅ Classic indicators calculated")

# ── Smart Money Concepts ─────────────────────────────────────

# 1. Swing Highs and Lows
df["Swing_High"] = df["High"][
    (df["High"] > df["High"].shift(1)) &
    (df["High"] > df["High"].shift(-1))
]
df["Swing_Low"] = df["Low"][
    (df["Low"] < df["Low"].shift(1)) &
    (df["Low"] < df["Low"].shift(-1))
]

# 2. Break of Structure
df["BOS_Bullish"] = (
    (df["Close"] > df["Swing_High"].ffill()) &
    (df["Close"].shift(1) <= df["Swing_High"].ffill().shift(1))
)
df["BOS_Bearish"] = (
    (df["Close"] < df["Swing_Low"].ffill()) &
    (df["Close"].shift(1) >= df["Swing_Low"].ffill().shift(1))
)

# 3. Order Blocks
df["Bullish_OB"] = (
    (df["Close"].shift(1) < df["Open"].shift(1)) &
    (df["Close"] > df["Open"]) &
    (df["Close"] > df["Close"].shift(1) * 1.01)
)
df["Bearish_OB"] = (
    (df["Close"].shift(1) > df["Open"].shift(1)) &
    (df["Close"] < df["Open"]) &
    (df["Close"] < df["Close"].shift(1) * 0.99)
)

# 4. Fair Value Gaps
df["FVG_Bullish"] = df["Low"] > df["High"].shift(2)
df["FVG_Bearish"] = df["High"] < df["Low"].shift(2)

# 5. Liquidity Zones
df["Liq_High"] = df["Swing_High"].ffill()
df["Liq_Low"]  = df["Swing_Low"].ffill()

print("✅ Smart Money Concepts calculated")
print(f"   Bullish BOS:          {df['BOS_Bullish'].sum()}")
print(f"   Bearish BOS:          {df['BOS_Bearish'].sum()}")
print(f"   Bullish Order Blocks: {df['Bullish_OB'].sum()}")
print(f"   Bearish Order Blocks: {df['Bearish_OB'].sum()}")
print(f"   Bullish FVGs:         {df['FVG_Bullish'].sum()}")
print(f"   Bearish FVGs:         {df['FVG_Bearish'].sum()}")

# ── Charts ───────────────────────────────────────────────────
fig, axes = plt.subplots(4, 1, figsize=(16, 20), sharex=True)
fig.suptitle("AAPL — Technical Analysis + Smart Money Concepts", fontsize=16)

# Chart 1: Price + SMC
ax1 = axes[0]
ax1.plot(df.index, df["Close"], color="white", linewidth=1, label="Close")
ax1.plot(df.index, df["EMA_20"], color="yellow", linewidth=0.8, label="EMA 20")
ax1.plot(df.index, df["EMA_50"], color="orange", linewidth=0.8, label="EMA 50")
ax1.plot(df.index, df["EMA_200"], color="red", linewidth=0.8, label="EMA 200")
ax1.fill_between(df.index, df["BB_Upper"], df["BB_Lower"],
                 alpha=0.1, color="cyan", label="Bollinger Bands")
ax1.plot(df.index, df["VWAP"], color="purple", linewidth=0.8,
         linestyle="--", label="VWAP")
ax1.scatter(df.index, df["Swing_High"], color="lime", marker="^",
            s=20, label="Swing High")
ax1.scatter(df.index, df["Swing_Low"], color="red", marker="v",
            s=20, label="Swing Low")
ax1.scatter(df.index[df["BOS_Bullish"]], df["Close"][df["BOS_Bullish"]],
            color="cyan", marker="*", s=100, label="BOS Bullish")
ax1.scatter(df.index[df["BOS_Bearish"]], df["Close"][df["BOS_Bearish"]],
            color="magenta", marker="*", s=100, label="BOS Bearish")
ax1.scatter(df.index[df["Bullish_OB"]], df["Close"][df["Bullish_OB"]],
            color="lime", marker="D", s=40, label="Bullish OB")
ax1.scatter(df.index[df["Bearish_OB"]], df["Close"][df["Bearish_OB"]],
            color="red", marker="D", s=40, label="Bearish OB")
ax1.scatter(df.index[df["FVG_Bullish"]], df["Close"][df["FVG_Bullish"]],
            color="cyan", marker="s", s=30, label="FVG Bullish")
ax1.scatter(df.index[df["FVG_Bearish"]], df["Close"][df["FVG_Bearish"]],
            color="magenta", marker="s", s=30, label="FVG Bearish")
ax1.set_facecolor("#1a1a2e")
ax1.set_ylabel("Price (USD)")
ax1.legend(loc="upper left", fontsize=6)
ax1.set_title("Price + Bollinger Bands + VWAP + SMC")
ax1.grid(True, alpha=0.2)

# Chart 2: RSI
ax2 = axes[1]
ax2.plot(df.index, df["RSI"], color="yellow", linewidth=1)
ax2.axhline(70, color="red", linestyle="--", linewidth=0.8, label="Overbought (70)")
ax2.axhline(30, color="lime", linestyle="--", linewidth=0.8, label="Oversold (30)")
ax2.fill_between(df.index, df["RSI"], 70,
                 where=(df["RSI"] >= 70), alpha=0.3, color="red")
ax2.fill_between(df.index, df["RSI"], 30,
                 where=(df["RSI"] <= 30), alpha=0.3, color="lime")
ax2.set_facecolor("#1a1a2e")
ax2.set_ylabel("RSI")
ax2.set_ylim(0, 100)
ax2.legend(fontsize=8)
ax2.set_title("RSI (14)")
ax2.grid(True, alpha=0.2)

# Chart 3: MACD
ax3 = axes[2]
ax3.plot(df.index, df["MACD"], color="cyan", linewidth=1, label="MACD")
ax3.plot(df.index, df["MACD_Signal"], color="orange", linewidth=1, label="Signal")
ax3.bar(df.index, df["MACD_Hist"],
        color=["lime" if v >= 0 else "red" for v in df["MACD_Hist"]],
        alpha=0.5, label="Histogram")
ax3.axhline(0, color="white", linewidth=0.5)
ax3.set_facecolor("#1a1a2e")
ax3.set_ylabel("MACD")
ax3.legend(fontsize=8)
ax3.set_title("MACD")
ax3.grid(True, alpha=0.2)

# Chart 4: Volume
ax4 = axes[3]
ax4.bar(df.index, df["Volume"],
        color=["lime" if df["Close"].iloc[i] >= df["Open"].iloc[i]
               else "red" for i in range(len(df))],
        alpha=0.7)
ax4.set_facecolor("#1a1a2e")
ax4.set_ylabel("Volume")
ax4.set_title("Volume")
ax4.grid(True, alpha=0.2)

fig.patch.set_facecolor("#0f0f23")
plt.tight_layout()
plt.savefig("data/AAPL_technical_analysis.png", dpi=150, bbox_inches="tight")
plt.show()
print("✅ Chart saved to data/AAPL_technical_analysis.png")