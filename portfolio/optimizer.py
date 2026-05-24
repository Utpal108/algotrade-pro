import pandas as pd
import numpy as np
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from universe.stocks import ALL_TICKERS, ALL_STOCKS
from universe.sectors import PORTFOLIO_RULES, SECTOR_LIMITS

# ════════════════════════════════════════════════════════════
# PORTFOLIO OPTIMIZER
# Combines factor scores with Mean Variance Optimization
# to find optimal portfolio weights
# ════════════════════════════════════════════════════════════

def load_price_data(ticker):
    """Load saved price data"""
    path = f"data/prices/{ticker.replace('.', '_')}.csv"
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.columns = ["Close", "High", "Low", "Open", "Volume"]
        return df.dropna().sort_index()
    except:
        return None

def calculate_returns_matrix():
    """
    Build a matrix of daily returns for all stocks
    Rows = dates, Columns = tickers
    """
    print("Building returns matrix...")
    returns_dict = {}

    for ticker in ALL_TICKERS:
        df = load_price_data(ticker)
        if df is not None:
            returns_dict[ticker] = df["Close"].pct_change().dropna()

    returns_matrix = pd.DataFrame(returns_dict).dropna()
    print(f"   Returns matrix: {returns_matrix.shape[0]} days x "
          f"{returns_matrix.shape[1]} stocks")
    return returns_matrix

def calculate_portfolio_metrics(weights, returns_matrix,
                                 risk_free_rate=0.04):
    """
    Calculate portfolio return, risk, and Sharpe ratio

    Formula:
    Portfolio Return = Σ(weight_i × mean_return_i) × 252
    Portfolio Risk   = √(w^T × Σ × w) × √252
    Sharpe Ratio     = (Return - Risk Free Rate) / Risk

    Where Σ is the covariance matrix
    """
    weights      = np.array(weights)
    mean_returns = returns_matrix.mean()
    cov_matrix   = returns_matrix.cov()

    # Annualized return
    port_return = np.sum(mean_returns * weights) * 252

    # Annualized risk (standard deviation)
    port_risk = np.sqrt(
        np.dot(weights.T, np.dot(cov_matrix * 252, weights))
    )

    # Sharpe ratio
    sharpe = ((port_return - risk_free_rate) / port_risk
              if port_risk > 0 else 0)

    return port_return, port_risk, sharpe

def optimize_portfolio(returns_matrix, factor_scores,
                       n_simulations=5000):
    """
    Monte Carlo Portfolio Optimization

    Theory — Modern Portfolio Theory (Markowitz 1952):
    Generate thousands of random portfolios and find
    the one with the best Sharpe Ratio (most return
    per unit of risk)

    The Efficient Frontier is the curve of optimal
    portfolios — maximum return for each level of risk
    """
    print(f"\nRunning Monte Carlo optimization "
          f"({n_simulations} simulations)...")

    tickers      = returns_matrix.columns.tolist()
    n_stocks     = len(tickers)
    mean_returns = returns_matrix.mean()
    cov_matrix   = returns_matrix.cov()

    # Get factor scores for weighting
    factor_dict = {}
    for _, row in factor_scores.iterrows():
        if row["Ticker"] in tickers:
            factor_dict[row["Ticker"]] = row["Composite"]

    results = {
        "returns":  [],
        "risks":    [],
        "sharpes":  [],
        "weights":  []
    }

    best_sharpe  = -999
    best_weights = None

    for i in range(n_simulations):
        # Generate random weights
        # Bias towards higher factor scores
        raw_weights = np.random.dirichlet(
            np.ones(n_stocks) * 2
        )

        # Apply factor bias — higher scored stocks
        # get slightly more weight
        factor_bias = np.array([
            factor_dict.get(t, 50) / 100
            for t in tickers
        ])
        biased_weights = raw_weights * factor_bias
        weights = biased_weights / biased_weights.sum()

        # Apply constraints
        # No single stock > 15%
        max_weight = PORTFOLIO_RULES["max_single_stock"]
        if np.max(weights) > max_weight:
            weights = np.clip(weights, 0, max_weight)
            weights = weights / weights.sum()

        # Calculate metrics
        ret, risk, sharpe = calculate_portfolio_metrics(
            weights, returns_matrix
        )

        results["returns"].append(ret)
        results["risks"].append(risk)
        results["sharpes"].append(sharpe)
        results["weights"].append(weights)

        if sharpe > best_sharpe:
            best_sharpe  = sharpe
            best_weights = weights

    print(f"   ✅ Best Sharpe Ratio: {best_sharpe:.3f}")
    return results, best_weights, tickers

def build_portfolio():
    """Build the optimal portfolio"""
    print("=" * 60)
    print("PORTFOLIO OPTIMIZER")
    print("=" * 60)

    # Load factor scores
    try:
        factor_scores = pd.read_csv("data/factor_scores.csv")
    except:
        print("❌ Run analysis/factors.py first")
        return None

    # Build returns matrix
    returns_matrix = calculate_returns_matrix()

    # Run optimization
    results, best_weights, tickers = optimize_portfolio(
        returns_matrix, factor_scores
    )

    # Calculate final portfolio metrics
    port_return, port_risk, sharpe = calculate_portfolio_metrics(
        best_weights, returns_matrix
    )

    # Build portfolio dataframe
    portfolio = []
    capital   = PORTFOLIO_RULES["starting_capital"]

    for ticker, weight in zip(tickers, best_weights):
        if weight > 0.001:  # only include meaningful positions
            info          = ALL_STOCKS.get(ticker, {})
            allocation    = weight * capital
            factor_row    = factor_scores[
                factor_scores["Ticker"] == ticker
            ]
            composite = (factor_row["Composite"].iloc[0]
                        if not factor_row.empty else 50)

            portfolio.append({
                "Ticker":      ticker,
                "Name":        info.get("name", ticker),
                "Sector":      info.get("sector", ""),
                "Market":      info.get("market", ""),
                "Weight":      round(weight * 100, 2),
                "Allocation":  round(allocation, 2),
                "Factor Score": round(composite, 1),
            })

    df_portfolio = pd.DataFrame(portfolio)
    df_portfolio = df_portfolio.sort_values(
        "Weight", ascending=False
    )

    # Save portfolio
    df_portfolio.to_csv("data/portfolio.csv", index=False)

    # Print results
    print("\n" + "=" * 60)
    print("OPTIMAL PORTFOLIO")
    print("=" * 60)
    print(f"\n{'Ticker':<8} {'Name':<25} {'Weight':>7} "
          f"{'Allocation':>12} {'Score':>7}")
    print("-" * 62)

    for _, row in df_portfolio.iterrows():
        print(f"{row['Ticker']:<8} {row['Name'][:24]:<25} "
              f"{row['Weight']:>6.1f}% "
              f"${row['Allocation']:>10,.0f} "
              f"{row['Factor Score']:>7.1f}")

    print("-" * 62)
    print(f"\n{'PORTFOLIO METRICS':}")
    print(f"   Expected Annual Return: {port_return*100:.2f}%")
    print(f"   Expected Annual Risk:   {port_risk*100:.2f}%")
    print(f"   Sharpe Ratio:           {sharpe:.3f}")
    print(f"   Total Capital:          "
          f"${capital:,.0f}")

    # Sector breakdown
    print(f"\n{'SECTOR BREAKDOWN':}")
    sector_weights = df_portfolio.groupby("Sector")["Weight"].sum()
    for sector, weight in sector_weights.sort_values(
            ascending=False).items():
        bar = "█" * int(weight / 2)
        print(f"   {sector:<25} {weight:>5.1f}% {bar}")

    # Market breakdown
    print(f"\n{'MARKET BREAKDOWN':}")
    market_weights = df_portfolio.groupby("Market")["Weight"].sum()
    for market, weight in market_weights.items():
        print(f"   {market:<10} {weight:>5.1f}%")

    print(f"\n✅ Portfolio saved to data/portfolio.csv")
    return df_portfolio

if __name__ == "__main__":
    build_portfolio()