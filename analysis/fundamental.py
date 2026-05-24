import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

# ── Load stock data ──────────────────────────────────────────
ticker = "AAPL"
stock  = yf.Ticker(ticker)
info   = stock.info

print(f"✅ Loaded data for {info.get('longName')}")

# ── Key Financial Ratios ─────────────────────────────────────
pe_ratio       = info.get("trailingPE", 0)
pb_ratio       = info.get("priceToBook", 0)
roe            = info.get("returnOnEquity", 0)
debt_to_equity = info.get("debtToEquity", 0)
profit_margin  = info.get("profitMargins", 0)
revenue_growth = info.get("revenueGrowth", 0)
eps            = info.get("trailingEps", 0)
current_price  = info.get("currentPrice", 0)

print("\n===== KEY FINANCIAL RATIOS =====")
print(f"P/E Ratio:        {pe_ratio:.2f}")
print(f"P/B Ratio:        {pb_ratio:.2f}")
print(f"ROE:              {roe*100:.2f}%")
print(f"Debt to Equity:   {debt_to_equity:.2f}")
print(f"Profit Margin:    {profit_margin*100:.2f}%")
print(f"Revenue Growth:   {revenue_growth*100:.2f}%")
print(f"EPS:              ${eps:.2f}")
print(f"Current Price:    ${current_price:.2f}")

# ── DCF Valuation ────────────────────────────────────────────
# Discounted Cash Flow — estimates intrinsic value
# Theory: a stock is worth the present value of all future cash flows

# Get free cash flow
cashflow       = stock.cashflow
free_cash_flow = cashflow.loc["Free Cash Flow"].iloc[0] \
                 if "Free Cash Flow" in cashflow.index else 0

# DCF assumptions
growth_rate    = 0.08   # 8% growth for next 10 years
discount_rate  = 0.10   # 10% required return (WACC)
terminal_growth= 0.03   # 3% terminal growth rate
shares_outstanding = info.get("sharesOutstanding", 1)

# Project cash flows for 10 years
projected_fcf = []
for year in range(1, 11):
    fcf = free_cash_flow * (1 + growth_rate) ** year
    projected_fcf.append(fcf)

# Discount each cash flow back to present value
pv_fcf = []
for year, fcf in enumerate(projected_fcf, 1):
    pv = fcf / (1 + discount_rate) ** year
    pv_fcf.append(pv)

# Terminal value (value beyond 10 years)
terminal_value = projected_fcf[-1] * (1 + terminal_growth) / \
                 (discount_rate - terminal_growth)
pv_terminal    = terminal_value / (1 + discount_rate) ** 10

# Intrinsic value per share
total_pv       = sum(pv_fcf) + pv_terminal
intrinsic_value= total_pv / shares_outstanding

print("\n===== DCF VALUATION =====")
print(f"Free Cash Flow:     ${free_cash_flow/1e9:.2f}B")
print(f"Intrinsic Value:    ${intrinsic_value:.2f}")
print(f"Current Price:      ${current_price:.2f}")
print(f"Margin of Safety:   {((intrinsic_value - current_price)/intrinsic_value)*100:.2f}%")

if current_price < intrinsic_value * 0.8:
    dcf_signal = "UNDERVALUED — Strong Buy"
elif current_price < intrinsic_value:
    dcf_signal = "FAIRLY VALUED — Hold"
else:
    dcf_signal = "OVERVALUED — Caution"

print(f"DCF Signal:         {dcf_signal}")

# ── Fundamental Scoring ──────────────────────────────────────
# Score the stock 0-100 based on financial health
score = 0

# P/E ratio (lower is better, under 25 is reasonable)
if pe_ratio < 15:   score += 20
elif pe_ratio < 25: score += 15
elif pe_ratio < 35: score += 10
else:               score += 0

# ROE (higher is better, over 15% is good)
if roe > 0.20:   score += 20
elif roe > 0.15: score += 15
elif roe > 0.10: score += 10
else:            score += 0

# Profit margin (higher is better)
if profit_margin > 0.20:   score += 20
elif profit_margin > 0.10: score += 15
elif profit_margin > 0.05: score += 10
else:                      score += 0

# Debt to equity (lower is better)
if debt_to_equity < 50:   score += 20
elif debt_to_equity < 100: score += 15
elif debt_to_equity < 200: score += 10
else:                      score += 0

# Revenue growth (higher is better)
if revenue_growth > 0.15:   score += 20
elif revenue_growth > 0.08: score += 15
elif revenue_growth > 0.03: score += 10
else:                       score += 0

print("\n===== FUNDAMENTAL SCORE =====")
print(f"Score: {score}/100")

if score >= 75:   fundamental_signal = "STRONG BUY"
elif score >= 60: fundamental_signal = "BUY"
elif score >= 40: fundamental_signal = "HOLD"
else:             fundamental_signal = "SELL"

print(f"Signal: {fundamental_signal}")

# ── Chart ────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle(f"AAPL — Fundamental Analysis", fontsize=14)

# Chart 1: Key ratios bar chart
metrics = ["P/E Ratio", "P/B Ratio", "ROE %", "Profit Margin %", "Revenue Growth %"]
values  = [pe_ratio, pb_ratio, roe*100, profit_margin*100, revenue_growth*100]
colors  = ["red" if v < 0 else "lime" for v in values]

axes[0].barh(metrics, values, color=colors, alpha=0.8)
axes[0].set_facecolor("#1a1a2e")
axes[0].set_title("Key Financial Ratios")
axes[0].grid(True, alpha=0.3)
axes[0].axvline(0, color="white", linewidth=0.5)

# Chart 2: DCF comparison
labels = ["Intrinsic Value", "Current Price"]
prices = [intrinsic_value, current_price]
colors = ["lime" if intrinsic_value > current_price else "red", "cyan"]

axes[1].bar(labels, prices, color=colors, alpha=0.8, width=0.4)
axes[1].set_facecolor("#1a1a2e")
axes[1].set_title(f"DCF Valuation vs Current Price\nSignal: {dcf_signal}")
axes[1].set_ylabel("Price (USD)")
axes[1].grid(True, alpha=0.3)

fig.patch.set_facecolor("#0f0f23")
plt.tight_layout()
plt.savefig("data/AAPL_fundamental_analysis.png", dpi=150, bbox_inches="tight")
plt.show()
print("\n✅ Fundamental analysis chart saved")