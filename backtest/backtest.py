import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ta
import warnings
warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════
# IMPROVED BACKTESTING ENGINE
# Uses a scoring system instead of strict conditions
# ════════════════════════════════════════════════════════════

print("Loading data...")
df = pd.read_csv("data/AAPL_raw.csv", skiprows=[1, 2],
                 index_col=0, parse_dates=True)
df.columns = ["Close", "High", "Low", "Open", "Volume"]
df = df.dropna().sort_index()

print(f"✅ Data loaded: {len(df)} trading days")
print(f"   From: {df.index[0].date()} To: {df.index[-1].date()}")

# ── Calculate Indicators ─────────────────────────────────────
print("\nCalculating indicators...")

df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()

macd = ta.trend.MACD(df["Close"])
df["MACD"]        = macd.macd()
df["MACD_Signal"] = macd.macd_signal()
df["MACD_Hist"]   = macd.macd_diff()

df["EMA_20"]  = ta.trend.EMAIndicator(df["Close"], window=20).ema_indicator()
df["EMA_50"]  = ta.trend.EMAIndicator(df["Close"], window=50).ema_indicator()
df["EMA_200"] = ta.trend.EMAIndicator(df["Close"], window=200).ema_indicator()

bb = ta.volatility.BollingerBands(df["Close"], window=20)
df["BB_Upper"] = bb.bollinger_hband()
df["BB_Lower"] = bb.bollinger_lband()
df["BB_Mid"]   = bb.bollinger_mavg()

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

# Daily returns
df["Daily_Return"] = df["Close"].pct_change()

print("✅ Indicators calculated")

# ── Scoring System ───────────────────────────────────────────
# Instead of strict conditions, score each day 0-100
# Buy when score is high, sell when score drops
print("\nGenerating scores...")

scores = []
for i in range(len(df)):
    row   = df.iloc[i]
    score = 50  # start neutral

    # RSI scoring
    rsi = row["RSI"]
    if rsi < 30:        score += 20  # oversold — strong buy
    elif rsi < 45:      score += 10  # healthy
    elif rsi < 60:      score += 5   # neutral
    elif rsi < 70:      score -= 5   # getting hot
    else:               score -= 20  # overbought — sell

    # MACD scoring
    if row["MACD"] > row["MACD_Signal"]:
        score += 15  # bullish momentum
        if row["MACD_Hist"] > 0 and df["MACD_Hist"].iloc[max(0,i-1)] <= 0:
            score += 10  # fresh bullish crossover — extra points
    else:
        score -= 15  # bearish momentum

    # Trend scoring
    close  = row["Close"]
    ema20  = row["EMA_20"]
    ema50  = row["EMA_50"]
    ema200 = row["EMA_200"]

    if close > ema200:  score += 10  # above long term trend
    else:               score -= 15  # below long term trend — dangerous

    if close > ema50:   score += 8
    else:               score -= 8

    if ema20 > ema50:   score += 7   # short term above medium term
    else:               score -= 7

    # Bollinger Band scoring
    if close < row["BB_Lower"]:  score += 15  # price at lower band — buy
    elif close > row["BB_Upper"]: score -= 15  # price at upper band — sell

    # SMC scoring
    if row["BOS_Bullish"]:  score += 10
    if row["Bullish_OB"]:   score += 8
    if row["FVG_Bullish"]:  score += 5

    scores.append(max(0, min(100, score)))  # clamp 0-100

df["Score"] = scores
df["Score"] = df["Score"].rolling(window=20).mean()
df["Score"] = df["Score"].fillna(50)

# ── Generate Signals from Score ──────────────────────────────
BUY_THRESHOLD    = 75  # very strict — only strongest signals
SELL_THRESHOLD   = 35  # very strict — only exit on clear weakness
MIN_HOLD_DAYS    = 60  # hold minimum 3 months

df["Buy_Signal"]  = df["Score"] >= BUY_THRESHOLD
df["Sell_Signal"] = df["Score"] <= SELL_THRESHOLD

print(f"   Buy signals:  {df['Buy_Signal'].sum()}")
print(f"   Sell signals: {df['Sell_Signal'].sum()}")

# ── Run Backtest ─────────────────────────────────────────────
print("\nRunning backtest...")

capital          = 100000
position         = 0
cash             = capital
portfolio_values = []
buy_dates        = []
sell_dates       = []
buy_prices       = []
sell_prices      = []
trades           = []
entry_price      = 0
stop_loss_pct    = 0.08   # 8% stop loss
take_profit_pct  = 0.25   # 25% take profit


hold_days = 0# tracks how long we've held current position

for i in range(200, len(df)):  # start after indicators warm up
    row   = df.iloc[i]
    price = row["Close"]
    
    if position > 0:
        hold_days += 1
    else:
        hold_days = 0

    # Check stop loss and take profit first
    # Check stop loss and take profit first
    if position > 0 and hold_days >= MIN_HOLD_DAYS:
        change = (price - entry_price) / entry_price

        # Stop loss hit
        if change <= -stop_loss_pct:
            cash     += position * price
            sell_dates.append(df.index[i])
            sell_prices.append(price)
            trades.append({
                "buy_price":  entry_price,
                "sell_price": price,
                "return_pct": change * 100,
                "exit_type":  "Stop Loss"
            })
            position = 0
            continue

        # Take profit hit
        if change >= take_profit_pct:
            cash     += position * price
            sell_dates.append(df.index[i])
            sell_prices.append(price)
            trades.append({
                "buy_price":  entry_price,
                "sell_price": price,
                "return_pct": change * 100,
                "exit_type":  "Take Profit"
            })
            position = 0
            continue

    # Buy signal
    if row["Buy_Signal"] and position == 0 and cash > price:
        shares_to_buy = int(cash * 0.95 / price)
        if shares_to_buy > 0:
            position    = shares_to_buy
            cash       -= shares_to_buy * price
            entry_price = price
            buy_dates.append(df.index[i])
            buy_prices.append(price)

    # Sell signal
    # Sell signal — only after minimum hold period
    elif row["Sell_Signal"] and position > 0 and hold_days >= MIN_HOLD_DAYS:
        change   = (price - entry_price) / entry_price
        cash    += position * price
        sell_dates.append(df.index[i])
        sell_prices.append(price)
        trades.append({
            "buy_price":  entry_price,
            "sell_price": price,
            "return_pct": change * 100,
            "exit_type":  "Signal"
        })
        position = 0

    portfolio_value = cash + position * price
    portfolio_values.append(portfolio_value)

# Close open position
if position > 0:
    final_price = df["Close"].iloc[-1]
    cash       += position * final_price
    portfolio_values[-1] = cash

# ── Performance Metrics ──────────────────────────────────────
portfolio_series = pd.Series(portfolio_values, index=df.index[200:200+len(portfolio_values)])
returns          = portfolio_series.pct_change().dropna()

total_return    = (cash - capital) / capital * 100
buy_hold_return = (df["Close"].iloc[-1] - df["Close"].iloc[200]) / \
                   df["Close"].iloc[200] * 100
sharpe_ratio    = (returns.mean() / returns.std()) * np.sqrt(252) \
                   if returns.std() > 0 else 0
rolling_max     = portfolio_series.cummax()
drawdown        = (portfolio_series - rolling_max) / rolling_max * 100
max_drawdown    = drawdown.min()

trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()
win_rate  = (trades_df["return_pct"] > 0).mean() * 100 \
             if len(trades_df) > 0 else 0
avg_return = trades_df["return_pct"].mean() \
              if len(trades_df) > 0 else 0

print("\n" + "=" * 50)
print("BACKTEST RESULTS")
print("=" * 50)
print(f"Starting Capital:   ${capital:,.2f}")
print(f"Final Capital:      ${cash:,.2f}")
print(f"Total Return:       {total_return:.2f}%")
print(f"Buy & Hold Return:  {buy_hold_return:.2f}%")
print(f"Sharpe Ratio:       {sharpe_ratio:.2f}")
print(f"Max Drawdown:       {max_drawdown:.2f}%")
print(f"Total Trades:       {len(trades_df)}")
print(f"Win Rate:           {win_rate:.1f}%")
print(f"Avg Trade Return:   {avg_return:.2f}%")

if len(trades_df) > 0:
    print(f"\nTrade Breakdown:")
    print(f"   Stop Loss exits:   "
          f"{(trades_df['exit_type']=='Stop Loss').sum()}")
    print(f"   Take Profit exits: "
          f"{(trades_df['exit_type']=='Take Profit').sum()}")
    print(f"   Signal exits:      "
          f"{(trades_df['exit_type']=='Signal').sum()}")
print("=" * 50)

if total_return > buy_hold_return:
    print("✅ Strategy BEAT buy and hold!")
else:
    print(f"⚠️  Strategy underperformed buy and hold by "
          f"{buy_hold_return - total_return:.2f}%")

# ── Charts ───────────────────────────────────────────────────
fig, axes = plt.subplots(4, 1, figsize=(16, 22), sharex=True)
fig.suptitle("AAPL — Improved Backtest Results", fontsize=16)

plot_df = df.iloc[200:]

# Chart 1: Price with signals
ax1 = axes[0]
ax1.plot(plot_df.index, plot_df["Close"],
         color="white", linewidth=1, label="Price")
ax1.plot(plot_df.index, plot_df["EMA_50"],
         color="orange", linewidth=0.8, label="EMA 50")
ax1.plot(plot_df.index, plot_df["EMA_200"],
         color="red", linewidth=0.8, label="EMA 200")
ax1.fill_between(plot_df.index, plot_df["BB_Upper"],
                 plot_df["BB_Lower"], alpha=0.1, color="cyan")
ax1.scatter(buy_dates, buy_prices, color="lime",
            marker="^", s=120, label="Buy", zorder=5)
ax1.scatter(sell_dates, sell_prices, color="red",
            marker="v", s=120, label="Sell", zorder=5)
ax1.set_facecolor("#1a1a2e")
ax1.set_ylabel("Price (USD)")
ax1.set_title("Price + Buy/Sell Signals")
ax1.legend(fontsize=8)
ax1.grid(True, alpha=0.2)

# Chart 2: Signal score
ax2 = axes[1]
ax2.plot(plot_df.index, plot_df["Score"],
         color="yellow", linewidth=1)
ax2.axhline(BUY_THRESHOLD, color="lime", linestyle="--",
            linewidth=1, label=f"Buy threshold ({BUY_THRESHOLD})")
ax2.axhline(SELL_THRESHOLD, color="red", linestyle="--",
            linewidth=1, label=f"Sell threshold ({SELL_THRESHOLD})")
ax2.fill_between(plot_df.index, plot_df["Score"], BUY_THRESHOLD,
                 where=(plot_df["Score"] >= BUY_THRESHOLD),
                 alpha=0.3, color="lime")
ax2.fill_between(plot_df.index, plot_df["Score"], SELL_THRESHOLD,
                 where=(plot_df["Score"] <= SELL_THRESHOLD),
                 alpha=0.3, color="red")
ax2.set_facecolor("#1a1a2e")
ax2.set_ylabel("Signal Score")
ax2.set_title("Composite Signal Score")
ax2.set_ylim(0, 100)
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.2)

# Chart 3: Portfolio vs buy and hold
ax3 = axes[2]
buy_hold_values = capital * (plot_df["Close"] / plot_df["Close"].iloc[0])
ax3.plot(portfolio_series.index, portfolio_series,
         color="cyan", linewidth=1.5, label="Our Strategy")
ax3.plot(plot_df.index, buy_hold_values,
         color="orange", linewidth=1.5, label="Buy & Hold")
ax3.set_facecolor("#1a1a2e")
ax3.set_ylabel("Portfolio Value ($)")
ax3.set_title("Strategy vs Buy & Hold")
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.2)

# Chart 4: Drawdown
ax4 = axes[3]
ax4.fill_between(drawdown.index, drawdown, 0, color="red", alpha=0.5)
ax4.plot(drawdown.index, drawdown, color="red", linewidth=0.8)
ax4.set_facecolor("#1a1a2e")
ax4.set_ylabel("Drawdown (%)")
ax4.set_title(f"Drawdown (Max: {max_drawdown:.2f}%)")
ax4.grid(True, alpha=0.2)

fig.patch.set_facecolor("#0f0f23")
plt.tight_layout()
plt.savefig("data/AAPL_backtest_improved.png", dpi=150, bbox_inches="tight")
plt.show()
print("\n✅ Improved backtest chart saved")