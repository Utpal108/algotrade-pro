import pandas as pd
import numpy as np
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from universe.stocks import ALL_TICKERS, ALL_STOCKS

# ════════════════════════════════════════════════════════════
# 7 FACTOR MODEL
# Ranks all 20 stocks across 7 factors
# ════════════════════════════════════════════════════════════

def load_price_data(ticker):
    """Load saved price data for a ticker"""
    path = f"data/prices/{ticker.replace('.', '_')}.csv"
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        df.columns = ["Close", "High", "Low", "Open", "Volume"]
        return df.dropna().sort_index()
    except:
        return None

def calculate_beta(stock_returns, market_returns):
    """
    Factor 1 — Beta (Market Sensitivity)
    Formula: Cov(stock, market) / Var(market)
    
    Beta = 1.0  → moves with market
    Beta > 1.0  → amplifies market moves (aggressive)
    Beta < 1.0  → defensive stock (stable)
    Beta < 0    → moves opposite to market (rare)
    """
    aligned = pd.concat([stock_returns, market_returns],
                        axis=1).dropna()
    if len(aligned) < 30:
        return 1.0
    cov    = aligned.cov().iloc[0, 1]
    var    = aligned.iloc[:, 1].var()
    return cov / var if var != 0 else 1.0

def calculate_momentum(df, months=12):
    """
    Factor 2 — Momentum (12 month price return)
    Formula: (Price now - Price 12 months ago) /
              Price 12 months ago × 100
    
    Theory: Stocks that went up in the last 12 months
    tend to keep going up (Jegadeesh & Titman 1993)
    """
    if len(df) < 252:
        return 0
    return ((df["Close"].iloc[-1] - df["Close"].iloc[-252]) /
             df["Close"].iloc[-252] * 100)

def calculate_value_score(fundamentals):
    """
    Factor 3 — Value (cheap vs expensive)
    Formula: Score based on P/E and P/B ratios
    
    Theory: Cheap stocks (low P/E, low P/B) outperform
    expensive stocks long term (Fama & French 1992)
    """
    score = 50  # start neutral
    pe = fundamentals.get("pe_ratio", 0)
    pb = fundamentals.get("pb_ratio", 0)

    # P/E scoring
    if 0 < pe < 15:   score += 25
    elif pe < 20:     score += 20
    elif pe < 25:     score += 15
    elif pe < 35:     score += 10
    elif pe > 35:     score += 0

    # P/B scoring
    if 0 < pb < 1:    score += 25
    elif pb < 2:      score += 20
    elif pb < 3:      score += 15
    elif pb < 5:      score += 10
    else:             score += 0

    return min(score, 100)

def calculate_quality_score(fundamentals):
    """
    Factor 4 — Quality (financial health)
    Formula: ROE + Profit Margin + low Debt

    Theory: High quality companies (high ROE, high margins,
    low debt) consistently outperform (Novy-Marx 2013)
    """
    score = 0
    roe    = fundamentals.get("roe", 0) or 0
    margin = fundamentals.get("profit_margin", 0) or 0
    de     = fundamentals.get("debt_to_equity", 0) or 0

    # ROE scoring
    if roe > 0.30:    score += 35
    elif roe > 0.20:  score += 30
    elif roe > 0.15:  score += 25
    elif roe > 0.10:  score += 15
    elif roe > 0:     score += 5

    # Profit margin scoring
    if margin > 0.25:  score += 35
    elif margin > 0.15: score += 28
    elif margin > 0.10: score += 20
    elif margin > 0.05: score += 12
    elif margin > 0:    score += 5

    # Debt scoring
    if de < 30:    score += 30
    elif de < 60:  score += 22
    elif de < 100: score += 15
    elif de < 150: score += 8
    else:          score += 0

    return min(score, 100)

def calculate_size_score(fundamentals):
    """
    Factor 5 — Size (market cap)
    Formula: Inverse of log(market cap)

    Theory: Smaller companies outperform larger ones
    long term (Fama & French 1992) — the size premium
    Note: We invert so smaller = higher score
    """
    market_cap = fundamentals.get("market_cap", 0) or 1
    if market_cap <= 0:
        return 50
    log_cap = np.log10(market_cap)

    # Scale: mega cap (>500B) = low score, small cap = high score
    if log_cap > 12:    return 20   # mega cap  >$1T
    elif log_cap > 11:  return 35   # large cap >$100B
    elif log_cap > 10:  return 55   # mid cap   >$10B
    elif log_cap > 9:   return 75   # small cap >$1B
    else:               return 90   # micro cap <$1B

def calculate_dividend_score(fundamentals):
    """
    Factor 6 — Dividend Yield
    Formula: Annual dividend / Stock price × 100

    Theory: Dividend paying stocks signal financial
    health and provide income regardless of price moves
    """
    div_yield = fundamentals.get("dividend_yield", 0) or 0
    div_yield = div_yield * 100  # convert to percentage

    if div_yield > 5:    return 100
    elif div_yield > 4:  return 85
    elif div_yield > 3:  return 70
    elif div_yield > 2:  return 55
    elif div_yield > 1:  return 40
    elif div_yield > 0:  return 25
    else:                return 10  # no dividend

def calculate_technical_score(df):
    """
    Factor 7 — Technical momentum score
    Uses RSI and moving averages
    """
    if df is None or len(df) < 200:
        return 50

    try:
        import ta
        close  = df["Close"]
        rsi    = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
        ema20  = ta.trend.EMAIndicator(close, window=20).ema_indicator().iloc[-1]
        ema50  = ta.trend.EMAIndicator(close, window=50).ema_indicator().iloc[-1]
        ema200 = ta.trend.EMAIndicator(close, window=200).ema_indicator().iloc[-1]
        macd   = ta.trend.MACD(close)
        macd_v = macd.macd().iloc[-1]
        macd_s = macd.macd_signal().iloc[-1]
        price  = close.iloc[-1]

        score = 50
        # RSI
        if rsi < 30:       score += 20
        elif rsi < 45:     score += 10
        elif rsi < 60:     score += 5
        elif rsi > 70:     score -= 15

        # MACD
        if macd_v > macd_s: score += 15
        else:               score -= 15

        # Trend
        if price > ema200:  score += 10
        if price > ema50:   score += 8
        if ema20 > ema50:   score += 7

        return max(0, min(100, score))
    except:
        return 50

def run_factor_model():
    """Run the full 7 factor model on all 20 stocks"""
    print("=" * 60)
    print("7 FACTOR MODEL — ALL 20 STOCKS")
    print("=" * 60)

    # Load fundamentals
    try:
        df_fund = pd.read_csv(
            "data/fundamentals/all_fundamentals.csv")
    except:
        print("❌ Fundamentals not found. Run fetch_data.py first")
        return None

    # Load market benchmark returns
    # Use S&P 500 as global benchmark
    try:
        import yfinance as yf
        mkt = yf.download("^GSPC", start="2020-01-01",
                          end="2024-12-31", progress=False)
        mkt_returns = mkt["Close"].pct_change().dropna()
    except:
        mkt_returns = pd.Series(dtype=float)

    results = []

    for ticker in ALL_TICKERS:
        print(f"\nAnalyzing {ticker}...")
        info = ALL_STOCKS[ticker]

        # Load price data
        df = load_price_data(ticker)

        # Get fundamentals
        fund_row = df_fund[df_fund["ticker"] == ticker]
        if fund_row.empty:
            fundamentals = {}
        else:
            fundamentals = fund_row.iloc[0].to_dict()

        # Calculate all 7 factors
        # Factor 1 — Beta
        if df is not None and len(mkt_returns) > 0:
            stock_returns = df["Close"].pct_change().dropna()
            beta = calculate_beta(stock_returns, mkt_returns)
            # Beta score: closer to 1 = better balanced
            beta_score = max(0, 100 - abs(beta - 1) * 30)
        else:
            beta = 1.0
            beta_score = 50

        # Factor 2 — Momentum
        momentum     = calculate_momentum(df) if df is not None else 0
        if momentum > 30:      momentum_score = 100
        elif momentum > 20:    momentum_score = 85
        elif momentum > 10:    momentum_score = 70
        elif momentum > 0:     momentum_score = 55
        elif momentum > -10:   momentum_score = 35
        else:                  momentum_score = 15

        # Factors 3-6
        value_score    = calculate_value_score(fundamentals)
        quality_score  = calculate_quality_score(fundamentals)
        size_score     = calculate_size_score(fundamentals)
        div_score      = calculate_dividend_score(fundamentals)

        # Factor 7 — Technical
        tech_score = calculate_technical_score(df)

        # Composite score
        # Weights: Quality 25%, Value 20%, Technical 20%,
        #          Momentum 15%, Dividend 10%, Beta 5%, Size 5%
        composite = (
            quality_score  * 0.25 +
            value_score    * 0.20 +
            tech_score     * 0.20 +
            momentum_score * 0.15 +
            div_score      * 0.10 +
            beta_score     * 0.05 +
            size_score     * 0.05
        )

        results.append({
            "Ticker":     ticker,
            "Name":       info["name"],
            "Sector":     info["sector"],
            "Market":     info["market"],
            "Beta":       round(beta, 2),
            "Momentum":   round(momentum, 1),
            "Value":      round(value_score, 1),
            "Quality":    round(quality_score, 1),
            "Size":       round(size_score, 1),
            "Dividend":   round(div_score, 1),
            "Technical":  round(tech_score, 1),
            "Composite":  round(composite, 1),
        })

    # Create results dataframe
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values("Composite",
                                         ascending=False)
    df_results["Rank"] = range(1, len(df_results) + 1)

    # Save results
    df_results.to_csv("data/factor_scores.csv", index=False)

    # Print results
    print("\n" + "=" * 60)
    print("FACTOR MODEL RESULTS — RANKED BY COMPOSITE SCORE")
    print("=" * 60)
    print(f"\n{'Rank':<5} {'Ticker':<8} {'Name':<25} "
          f"{'Quality':<9} {'Value':<7} {'Tech':<7} "
          f"{'Momentum':<9} {'Composite':<10}")
    print("-" * 75)

    for _, row in df_results.iterrows():
        print(f"{row['Rank']:<5} {row['Ticker']:<8} "
              f"{row['Name'][:24]:<25} "
              f"{row['Quality']:<9} {row['Value']:<7} "
              f"{row['Technical']:<7} {row['Momentum']:<9} "
              f"{row['Composite']:<10}")

    print("\n✅ Factor scores saved to data/factor_scores.csv")
    return df_results

if __name__ == "__main__":
    df = run_factor_model()