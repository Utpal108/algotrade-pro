import yfinance as yf
import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from universe.stocks import ALL_TICKERS, ALL_STOCKS

# ════════════════════════════════════════════════════════════
# DATA FETCHER — Downloads data for all 20 stocks
# ════════════════════════════════════════════════════════════

START_DATE = "2020-01-01"
END_DATE   = "2024-12-31"

def fetch_price_data(ticker, start=START_DATE, end=END_DATE):
    """Fetch OHLCV data for a single ticker"""
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df.empty:
            print(f"   ⚠️  No data for {ticker}")
            return None
        df.columns = ["Close", "High", "Low", "Open", "Volume"]
        df = df.dropna().sort_index()
        return df
    except Exception as e:
        print(f"   ❌ Error fetching {ticker}: {e}")
        return None

def fetch_fundamental_data(ticker):
    """Fetch fundamental data for a single ticker"""
    try:
        stock = yf.Ticker(ticker)
        info  = stock.info
        return {
            "ticker":          ticker,
            "name":            info.get("longName", ""),
            "sector":          info.get("sector", ""),
            "market_cap":      info.get("marketCap", 0),
            "pe_ratio":        info.get("trailingPE", 0),
            "pb_ratio":        info.get("priceToBook", 0),
            "roe":             info.get("returnOnEquity", 0),
            "profit_margin":   info.get("profitMargins", 0),
            "revenue_growth":  info.get("revenueGrowth", 0),
            "debt_to_equity":  info.get("debtToEquity", 0),
            "dividend_yield":  info.get("dividendYield", 0),
            "current_price":   info.get("currentPrice", 0),
            "52w_high":        info.get("fiftyTwoWeekHigh", 0),
            "52w_low":         info.get("fiftyTwoWeekLow", 0),
            "eps":             info.get("trailingEps", 0),
            "beta":            info.get("beta", 1),
        }
    except Exception as e:
        print(f"   ❌ Error fetching fundamentals for {ticker}: {e}")
        return None

def fetch_all_data():
    """Fetch data for all 20 stocks"""
    print("=" * 50)
    print("FETCHING DATA FOR ALL 20 STOCKS")
    print("=" * 50)

    # Create data directory
    os.makedirs("data/prices",       exist_ok=True)
    os.makedirs("data/fundamentals", exist_ok=True)

    # Fetch price data
    print("\n📈 Fetching price data...")
    price_success = []
    price_failed  = []

    for ticker in ALL_TICKERS:
        name = ALL_STOCKS[ticker]["name"]
        print(f"   Fetching {ticker} ({name})...")
        df = fetch_price_data(ticker)
        if df is not None:
            df.to_csv(f"data/prices/{ticker.replace('.', '_')}.csv")
            price_success.append(ticker)
        else:
            price_failed.append(ticker)

    print(f"\n   ✅ Price data: {len(price_success)}/20 successful")
    if price_failed:
        print(f"   ⚠️  Failed: {price_failed}")

    # Fetch fundamental data
    print("\n🏦 Fetching fundamental data...")
    fundamentals = []
    fund_success  = []
    fund_failed   = []

    for ticker in ALL_TICKERS:
        name = ALL_STOCKS[ticker]["name"]
        print(f"   Fetching {ticker} ({name})...")
        data = fetch_fundamental_data(ticker)
        if data is not None:
            fundamentals.append(data)
            fund_success.append(ticker)
        else:
            fund_failed.append(ticker)

    # Save all fundamentals in one file
    if fundamentals:
        df_fund = pd.DataFrame(fundamentals)
        df_fund.to_csv("data/fundamentals/all_fundamentals.csv",
                       index=False)
        print(f"\n   ✅ Fundamental data: {len(fund_success)}/20 successful")

    if fund_failed:
        print(f"   ⚠️  Failed: {fund_failed}")

    # Summary
    print("\n" + "=" * 50)
    print("DATA FETCH COMPLETE")
    print("=" * 50)
    print(f"Price files saved to:       data/prices/")
    print(f"Fundamentals saved to:      data/fundamentals/")
    print(f"Total stocks fetched:       {len(price_success)}")

    return price_success

if __name__ == "__main__":
    fetch_all_data()