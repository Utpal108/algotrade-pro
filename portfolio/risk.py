import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from universe.stocks import ALL_TICKERS, ALL_STOCKS

# ════════════════════════════════════════════════════════════
# RISK MANAGEMENT MODULE
# VaR, Correlation, Drawdown, Concentration Risk
# ════════════════════════════════════════════════════════════

def load_price_data(ticker):
    path = f"data/prices/{ticker.replace('.', '_')}.csv"
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.columns = ["Close", "High", "Low", "Open", "Volume"]
        return df.dropna().sort_index()
    except:
        return None

def calculate_var(returns, confidence=0.95, capital=100000):
    """
    Value at Risk (VaR) — Historical Method

    Definition: The maximum loss not exceeded with
    a given probability over a specific time period.

    Formula:
    VaR(95%) = 5th percentile of return distribution × Capital

    Example:
    VaR(95%) = -2.5% means there is a 95% chance
    you will NOT lose more than $2,500 on any given day

    Regulatory standard: Banks must hold capital equal
    to 10 day VaR at 99% confidence (Basel III)
    """
    var_pct    = np.percentile(returns, (1 - confidence) * 100)
    var_dollar = var_pct * capital
    return var_pct, var_dollar

def calculate_cvar(returns, confidence=0.95, capital=100000):
    """
    Conditional VaR (CVaR) / Expected Shortfall

    Definition: The AVERAGE loss when losses exceed VaR.
    More conservative than VaR — tells you how bad
    it gets in the worst cases.

    Formula:
    CVaR = Mean of returns below VaR threshold
    """
    var_pct  = np.percentile(returns, (1 - confidence) * 100)
    cvar_pct = returns[returns <= var_pct].mean()
    cvar_dollar = cvar_pct * capital
    return cvar_pct, cvar_dollar

def calculate_max_drawdown(portfolio_values):
    """
    Maximum Drawdown

    Definition: Largest peak to trough decline
    in portfolio value.

    Formula:
    Drawdown     = (Current Value - Peak Value) / Peak Value
    Max Drawdown = Minimum of all drawdowns

    Example:
    Portfolio peaks at $150,000 then drops to $120,000
    Max Drawdown = (120,000 - 150,000) / 150,000 = -20%
    """
    portfolio_series = pd.Series(portfolio_values)
    rolling_max      = portfolio_series.cummax()
    drawdown         = (portfolio_series - rolling_max) / rolling_max
    return drawdown.min() * 100

def build_correlation_matrix(returns_dict):
    """
    Correlation Matrix

    Definition: Measures how stocks move together.
    Range: -1 to +1

    +1.0 = Perfect positive correlation (move identically)
     0.0 = No correlation (move independently)
    -1.0 = Perfect negative correlation (move opposite)

    Portfolio theory: Combine LOW correlation assets
    to reduce risk without sacrificing return.
    This is the core of diversification.
    """
    returns_df = pd.DataFrame(returns_dict).dropna()
    return returns_df.corr()

def run_risk_analysis():
    """Run complete risk analysis on the portfolio"""
    print("=" * 60)
    print("RISK MANAGEMENT ANALYSIS")
    print("=" * 60)

    # Load portfolio
    try:
        portfolio = pd.read_csv("data/portfolio.csv")
    except:
        print("❌ Run portfolio/optimizer.py first")
        return

    capital = 100000

    # Build returns for portfolio stocks
    print("\nLoading price data...")
    returns_dict   = {}
    weights_dict   = {}

    for _, row in portfolio.iterrows():
        ticker = row["Ticker"]
        weight = row["Weight"] / 100
        df     = load_price_data(ticker)
        if df is not None:
            returns_dict[ticker] = df["Close"].pct_change().dropna()
            weights_dict[ticker] = weight

    # Align all returns to same dates
    returns_df = pd.DataFrame(returns_dict).dropna()

    # Calculate portfolio returns
    weights_array  = np.array([
        weights_dict.get(t, 0)
        for t in returns_df.columns
    ])
    weights_array  = weights_array / weights_array.sum()
    port_returns   = returns_df.dot(weights_array)

    # ── VaR Analysis ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("VALUE AT RISK (VaR)")
    print("=" * 60)

    var95_pct,  var95_dollar  = calculate_var(
        port_returns, 0.95, capital)
    var99_pct,  var99_dollar  = calculate_var(
        port_returns, 0.99, capital)
    cvar95_pct, cvar95_dollar = calculate_cvar(
        port_returns, 0.95, capital)

    print(f"\n   Daily VaR (95%):  {var95_pct*100:.2f}%  "
          f"= ${abs(var95_dollar):,.0f}")
    print(f"   Daily VaR (99%):  {var99_pct*100:.2f}%  "
          f"= ${abs(var99_dollar):,.0f}")
    print(f"   Daily CVaR (95%): {cvar95_pct*100:.2f}% "
          f"= ${abs(cvar95_dollar):,.0f}")

    print(f"\n   Interpretation:")
    print(f"   On 95% of trading days your portfolio")
    print(f"   will NOT lose more than "
          f"${abs(var95_dollar):,.0f} in a single day")
    print(f"   On your worst days (top 5%) the average")
    print(f"   loss will be ${abs(cvar95_dollar):,.0f}")

    # ── Drawdown Analysis ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("DRAWDOWN ANALYSIS")
    print("=" * 60)

    portfolio_values = capital * (1 + port_returns).cumprod()
    max_dd           = calculate_max_drawdown(portfolio_values)
    current_value    = portfolio_values.iloc[-1]
    total_return     = (current_value - capital) / capital * 100

    print(f"\n   Starting Capital:  ${capital:,.0f}")
    print(f"   Current Value:     ${current_value:,.0f}")
    print(f"   Total Return:      {total_return:.2f}%")
    print(f"   Max Drawdown:      {max_dd:.2f}%")
    print(f"   Max $ Drawdown:    "
          f"${abs(max_dd/100 * capital):,.0f}")

    # ── Correlation Analysis ──────────────────────────────────
    print("\n" + "=" * 60)
    print("CORRELATION ANALYSIS")
    print("=" * 60)

    corr_matrix = build_correlation_matrix(returns_dict)

    # Find highest and lowest correlations
    corr_pairs = []
    tickers    = list(returns_dict.keys())
    for i in range(len(tickers)):
        for j in range(i+1, len(tickers)):
            t1   = tickers[i]
            t2   = tickers[j]
            corr = corr_matrix.loc[t1, t2]
            corr_pairs.append((t1, t2, corr))

    corr_pairs.sort(key=lambda x: x[2], reverse=True)

    print("\n   Highest correlations (move together):")
    for t1, t2, corr in corr_pairs[:5]:
        print(f"   {t1:<8} + {t2:<8} = {corr:.3f}")

    print("\n   Lowest correlations (best diversifiers):")
    for t1, t2, corr in corr_pairs[-5:]:
        print(f"   {t1:<8} + {t2:<8} = {corr:.3f}")

    # ── Concentration Risk ────────────────────────────────────
    print("\n" + "=" * 60)
    print("CONCENTRATION RISK")
    print("=" * 60)

    print("\n   Top 5 positions:")
    for _, row in portfolio.head(5).iterrows():
        bar = "█" * int(row["Weight"])
        print(f"   {row['Ticker']:<8} {row['Weight']:>5.1f}% {bar}")

    top5_weight = portfolio.head(5)["Weight"].sum()
    print(f"\n   Top 5 concentration: {top5_weight:.1f}%")

    if top5_weight > 50:
        print("   ⚠️  High concentration — top 5 stocks")
        print("       hold more than half the portfolio")
    else:
        print("   ✅ Acceptable concentration")

    # ── Save risk metrics ─────────────────────────────────────
    risk_metrics = {
        "var_95_pct":     var95_pct * 100,
        "var_95_dollar":  abs(var95_dollar),
        "var_99_pct":     var99_pct * 100,
        "var_99_dollar":  abs(var99_dollar),
        "cvar_95_pct":    cvar95_pct * 100,
        "cvar_95_dollar": abs(cvar95_dollar),
        "max_drawdown":   max_dd,
        "total_return":   total_return,
        "current_value":  current_value,
    }

    pd.DataFrame([risk_metrics]).to_csv(
        "data/risk_metrics.csv", index=False)

    # ── Charts ────────────────────────────────────────────────
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Portfolio Risk Dashboard", fontsize=16)
    fig.patch.set_facecolor("#0f0f23")

    # Chart 1: Portfolio value over time
    ax1 = axes[0, 0]
    ax1.plot(portfolio_values.index, portfolio_values,
             color="cyan", linewidth=1.5)
    ax1.axhline(capital, color="white", linestyle="--",
                linewidth=0.8, label="Starting Capital")
    ax1.fill_between(portfolio_values.index,
                     portfolio_values, capital,
                     where=(portfolio_values >= capital),
                     alpha=0.3, color="lime")
    ax1.fill_between(portfolio_values.index,
                     portfolio_values, capital,
                     where=(portfolio_values < capital),
                     alpha=0.3, color="red")
    ax1.set_facecolor("#1a1a2e")
    ax1.set_title("Portfolio Value Over Time", color="white")
    ax1.set_ylabel("Value ($)", color="white")
    ax1.tick_params(colors="white")
    ax1.grid(True, alpha=0.2)
    ax1.legend(fontsize=8)

    # Chart 2: Return distribution + VaR
    ax2 = axes[0, 1]
    ax2.hist(port_returns * 100, bins=50,
             color="cyan", alpha=0.7, edgecolor="none")
    ax2.axvline(var95_pct * 100, color="orange",
                linestyle="--", linewidth=1.5,
                label=f"VaR 95%: {var95_pct*100:.2f}%")
    ax2.axvline(var99_pct * 100, color="red",
                linestyle="--", linewidth=1.5,
                label=f"VaR 99%: {var99_pct*100:.2f}%")
    ax2.set_facecolor("#1a1a2e")
    ax2.set_title("Daily Return Distribution", color="white")
    ax2.set_xlabel("Daily Return (%)", color="white")
    ax2.tick_params(colors="white")
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.2)

    # Chart 3: Drawdown
    rolling_max = portfolio_values.cummax()
    drawdown    = (portfolio_values - rolling_max) / rolling_max * 100
    ax3 = axes[1, 0]
    ax3.fill_between(drawdown.index, drawdown, 0,
                     color="red", alpha=0.5)
    ax3.plot(drawdown.index, drawdown,
             color="red", linewidth=0.8)
    ax3.set_facecolor("#1a1a2e")
    ax3.set_title(f"Drawdown (Max: {max_dd:.2f}%)",
                  color="white")
    ax3.set_ylabel("Drawdown (%)", color="white")
    ax3.tick_params(colors="white")
    ax3.grid(True, alpha=0.2)

    # Chart 4: Correlation heatmap
    ax4 = axes[1, 1]
    tickers_short = [t.replace(".AX", "") for t in corr_matrix.columns]
    im = ax4.imshow(corr_matrix.values,
                    cmap="RdYlGn", vmin=-1, vmax=1)
    ax4.set_xticks(range(len(tickers_short)))
    ax4.set_yticks(range(len(tickers_short)))
    ax4.set_xticklabels(tickers_short, rotation=45,
                        fontsize=7, color="white")
    ax4.set_yticklabels(tickers_short,
                        fontsize=7, color="white")
    ax4.set_title("Correlation Matrix", color="white")
    plt.colorbar(im, ax=ax4)

    plt.tight_layout()
    plt.savefig("data/risk_dashboard.png",
                dpi=150, bbox_inches="tight")
    plt.show()
    print("\n✅ Risk analysis complete")
    print("✅ Chart saved to data/risk_dashboard.png")
    print("✅ Metrics saved to data/risk_metrics.csv")

if __name__ == "__main__":
    run_risk_analysis()