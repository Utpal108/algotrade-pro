import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
from universe.stocks import ALL_TICKERS, ALL_STOCKS

# ════════════════════════════════════════════════════════════
# REAL TIME DATA MODULE
# Fetches live prices during market hours
# ════════════════════════════════════════════════════════════

def is_market_open(market="US"):
    """Check if market is currently open"""
    now = datetime.now(timezone.utc)
    weekday = now.weekday()  # 0=Monday, 6=Sunday

    # Weekend check
    if weekday >= 5:
        return False

    hour = now.hour
    minute = now.minute

    if market == "US":
        # NYSE: 9:30 AM - 4:00 PM EST = 14:30-21:00 UTC
        market_open  = hour * 60 + minute >= 14 * 60 + 30
        market_close = hour * 60 + minute <= 21 * 60
        return market_open and market_close

    elif market == "ASX":
        # ASX: 10:00 AM - 4:00 PM AEST = 00:00-06:00 UTC
        market_open  = hour * 60 + minute >= 0
        market_close = hour * 60 + minute <= 6 * 60
        return market_open and market_close

    return False

def get_live_price(ticker):
    """
    Get real time price for a single ticker
    Returns current price, change, change %
    """
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info

        current_price  = info.get("currentPrice") or \
                         info.get("regularMarketPrice") or \
                         info.get("previousClose", 0)
        previous_close = info.get("previousClose",
                                   current_price)
        change         = current_price - previous_close
        change_pct     = (change / previous_close * 100
                          if previous_close > 0 else 0)
        volume         = info.get("regularMarketVolume", 0)
        day_high       = info.get("dayHigh",
                                   info.get("regularMarketDayHigh", 0))
        day_low        = info.get("dayLow",
                                   info.get("regularMarketDayLow", 0))

        market = ALL_STOCKS.get(ticker, {}).get("market", "SP500")
        is_open = is_market_open(
            "ASX" if market == "ASX" else "US"
        )

        return {
            "ticker":         ticker,
            "name":           ALL_STOCKS.get(ticker, {}).get("name", ticker),
            "price":          round(current_price, 2),
            "change":         round(change, 2),
            "change_pct":     round(change_pct, 2),
            "volume":         volume,
            "day_high":       round(day_high, 2),
            "day_low":        round(day_low, 2),
            "previous_close": round(previous_close, 2),
            "market_open":    is_open,
            "currency":       ALL_STOCKS.get(
                ticker, {}).get("currency", "USD"),
            "timestamp":      datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {
            "ticker":     ticker,
            "name":       ticker,
            "price":      0,
            "change":     0,
            "change_pct": 0,
            "error":      str(e)
        }

def get_all_live_prices():
    """Get live prices for all 20 stocks"""
    print("Fetching live prices for all 20 stocks...")
    results = []
    for ticker in ALL_TICKERS:
        data = get_live_price(ticker)
        results.append(data)
        status = "🟢" if data.get("change_pct", 0) >= 0 else "🔴"
        print(f"  {status} {ticker:<8} "
              f"${data.get('price', 0):.2f} "
              f"({data.get('change_pct', 0):+.2f}%)")

    df = pd.DataFrame(results)
    df.to_csv("data/live_prices.csv", index=False)
    print(f"\n✅ Live prices saved to data/live_prices.csv")
    return df

def get_intraday_data(ticker, period="1d", interval="5m"):
    """
    Get intraday price data for live chart
    period:   1d, 5d
    interval: 1m, 5m, 15m, 30m, 1h
    """
    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            progress=False
        )
        if df.empty:
            return None
        df.columns = ["Close", "High", "Low", "Open", "Volume"]
        return df.dropna()
    except:
        return None

def calculate_portfolio_live_value(portfolio_csv="data/portfolio.csv"):
    """
    Calculate current live portfolio value
    using real time prices
    """
    try:
        portfolio = pd.read_csv(portfolio_csv)
        capital   = 100000
        total_value = 0
        positions   = []

        for _, row in portfolio.iterrows():
            ticker     = row["Ticker"]
            weight     = row["Weight"] / 100
            allocation = weight * capital
            live       = get_live_price(ticker)
            price      = live.get("price", 0)
            prev_close = live.get("previous_close", price)

            # Calculate current value
            # Assume we bought at start price from CSV
            try:
                hist = pd.read_csv(
                    f"data/prices/{ticker.replace('.','_')}.csv",
                    index_col=0, parse_dates=True
                )
                hist.columns = ["Close","High","Low","Open","Volume"]
                buy_price = hist["Close"].iloc[0]
                shares    = allocation / buy_price
                curr_value = shares * price
            except:
                curr_value = allocation * (
                    price / prev_close if prev_close > 0 else 1
                )

            change_pct = live.get("change_pct", 0)
            total_value += curr_value

            positions.append({
                "Ticker":       ticker,
                "Name":         row["Name"],
                "Weight":       f"{weight*100:.1f}%",
                "Live Price":   f"${price:.2f}",
                "Change":       f"{change_pct:+.2f}%",
                "Curr Value":   f"${curr_value:,.0f}",
                "Market Open":  live.get("market_open", False)
            })

        return total_value, pd.DataFrame(positions)

    except Exception as e:
        print(f"Error calculating live value: {e}")
        return 0, pd.DataFrame()

if __name__ == "__main__":
    print("=" * 50)
    print("LIVE MARKET DATA")
    print("=" * 50)
    print(f"\nUS Market open:  {is_market_open('US')}")
    print(f"ASX Market open: {is_market_open('ASX')}")
    df = get_all_live_prices()
    print("\nTop movers today:")
    df_sorted = df.sort_values("change_pct", ascending=False)
    print(df_sorted[["ticker","price","change_pct"]].head(5))