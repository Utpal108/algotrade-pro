import yfinance as yf

# Define the stock
ticker = "AAPL"
stock  = yf.Ticker(ticker)

# Income statement
print("===== INCOME STATEMENT =====")
print(stock.financials)

# Balance sheet
print("\n===== BALANCE SHEET =====")
print(stock.balance_sheet)

# Cash flow statement
print("\n===== CASH FLOW =====")
print(stock.cashflow)

# Key ratios and info
print("\n===== KEY METRICS =====")
info = stock.info
print(f"Company:              {info.get('longName')}")
print(f"Sector:               {info.get('sector')}")
print(f"Market Cap:           ${info.get('marketCap'):,}")
print(f"P/E Ratio:            {info.get('trailingPE')}")
print(f"EPS:                  {info.get('trailingEps')}")
print(f"Revenue:              ${info.get('totalRevenue'):,}")
print(f"Profit Margin:        {info.get('profitMargins')}")
print(f"Return on Equity:     {info.get('returnOnEquity')}")
print(f"Debt to Equity:       {info.get('debtToEquity')}")
print(f"Dividend Yield:       {info.get('dividendYield')}")
print(f"52 Week High:         {info.get('fiftyTwoWeekHigh')}")
print(f"52 Week Low:          {info.get('fiftyTwoWeekLow')}")

print("\n✅ Fundamental data loaded successfully")
import pandas as pd

# Save financials to CSV
stock.financials.to_csv("data/AAPL_income_statement.csv")
stock.balance_sheet.to_csv("data/AAPL_balance_sheet.csv")
stock.cashflow.to_csv("data/AAPL_cashflow.csv")

# Save key metrics to CSV
metrics = {
    "Company":          info.get("longName"),
    "Sector":           info.get("sector"),
    "Market Cap":       info.get("marketCap"),
    "P/E Ratio":        info.get("trailingPE"),
    "EPS":              info.get("trailingEps"),
    "Revenue":          info.get("totalRevenue"),
    "Profit Margin":    info.get("profitMargins"),
    "Return on Equity": info.get("returnOnEquity"),
    "Debt to Equity":   info.get("debtToEquity"),
    "Dividend Yield":   info.get("dividendYield"),
    "52 Week High":     info.get("fiftyTwoWeekHigh"),
    "52 Week Low":      info.get("fiftyTwoWeekLow"),
}

pd.DataFrame([metrics]).to_csv("data/AAPL_key_metrics.csv", index=False)
print("✅ All fundamental data saved to data/ folder")