# ════════════════════════════════════════════════════════════
# STOCK UNIVERSE — ASX 10 + S&P 10
# ════════════════════════════════════════════════════════════

# ASX stocks (Australian Securities Exchange)
ASX_STOCKS = {
    "CBA.AX": {
        "name":     "Commonwealth Bank",
        "sector":   "Financials",
        "market":   "ASX",
        "currency": "AUD"
    },
    "BHP.AX": {
        "name":     "BHP Group",
        "sector":   "Materials",
        "market":   "ASX",
        "currency": "AUD"
    },
    "CSL.AX": {
        "name":     "CSL Limited",
        "sector":   "Healthcare",
        "market":   "ASX",
        "currency": "AUD"
    },
    "WBC.AX": {
        "name":     "Westpac",
        "sector":   "Financials",
        "market":   "ASX",
        "currency": "AUD"
    },
    "ANZ.AX": {
        "name":     "ANZ Bank",
        "sector":   "Financials",
        "market":   "ASX",
        "currency": "AUD"
    },
    "WES.AX": {
        "name":     "Wesfarmers",
        "sector":   "Consumer Discretionary",
        "market":   "ASX",
        "currency": "AUD"
    },
    "TLS.AX": {
        "name":     "Telstra",
        "sector":   "Communication",
        "market":   "ASX",
        "currency": "AUD"
    },
    "RIO.AX": {
        "name":     "Rio Tinto",
        "sector":   "Materials",
        "market":   "ASX",
        "currency": "AUD"
    },
    "FMG.AX": {
        "name":     "Fortescue Metals",
        "sector":   "Materials",
        "market":   "ASX",
        "currency": "AUD"
    },
    "MQG.AX": {
        "name":     "Macquarie Group",
        "sector":   "Financials",
        "market":   "ASX",
        "currency": "AUD"
    },
}

# S&P stocks (US Market)
SP_STOCKS = {
    "AAPL": {
        "name":     "Apple",
        "sector":   "Technology",
        "market":   "SP500",
        "currency": "USD"
    },
    "MSFT": {
        "name":     "Microsoft",
        "sector":   "Technology",
        "market":   "SP500",
        "currency": "USD"
    },
    "GOOGL": {
        "name":     "Alphabet",
        "sector":   "Technology",
        "market":   "SP500",
        "currency": "USD"
    },
    "AMZN": {
        "name":     "Amazon",
        "sector":   "Consumer Discretionary",
        "market":   "SP500",
        "currency": "USD"
    },
    "NVDA": {
        "name":     "Nvidia",
        "sector":   "Technology",
        "market":   "SP500",
        "currency": "USD"
    },
    "JPM": {
        "name":     "JPMorgan Chase",
        "sector":   "Financials",
        "market":   "SP500",
        "currency": "USD"
    },
    "JNJ": {
        "name":     "Johnson and Johnson",
        "sector":   "Healthcare",
        "market":   "SP500",
        "currency": "USD"
    },
    "XOM": {
        "name":     "ExxonMobil",
        "sector":   "Energy",
        "market":   "SP500",
        "currency": "USD"
    },
    "BRK-B": {
        "name":     "Berkshire Hathaway",
        "sector":   "Financials",
        "market":   "SP500",
        "currency": "USD"
    },
    "V": {
        "name":     "Visa",
        "sector":   "Financials",
        "market":   "SP500",
        "currency": "USD"
    },
}

# Combined universe
ALL_STOCKS = {**ASX_STOCKS, **SP_STOCKS}

# Just the ticker symbols
ALL_TICKERS = list(ALL_STOCKS.keys())
ASX_TICKERS = list(ASX_STOCKS.keys())
SP_TICKERS  = list(SP_STOCKS.keys())

# Sector groupings
SECTORS = {}
for ticker, info in ALL_STOCKS.items():
    sector = info["sector"]
    if sector not in SECTORS:
        SECTORS[sector] = []
    SECTORS[sector].append(ticker)

if __name__ == "__main__":
    print("=" * 50)
    print("STOCK UNIVERSE")
    print("=" * 50)
    print(f"\nTotal stocks: {len(ALL_STOCKS)}")
    print(f"ASX stocks:   {len(ASX_STOCKS)}")
    print(f"S&P stocks:   {len(SP_STOCKS)}")
    print("\nSector breakdown:")
    for sector, tickers in SECTORS.items():
        print(f"  {sector}: {', '.join(tickers)}")
    print("\nAll tickers:")
    print(ALL_TICKERS)