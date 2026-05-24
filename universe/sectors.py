# ════════════════════════════════════════════════════════════
# SECTOR DEFINITIONS AND LIMITS
# ════════════════════════════════════════════════════════════

# Maximum portfolio allocation per sector (risk control)
SECTOR_LIMITS = {
    "Financials":             0.35,  # max 35% in financials
    "Technology":             0.35,  # max 35% in tech
    "Materials":              0.25,  # max 25% in mining/materials
    "Healthcare":             0.25,  # max 25% in healthcare
    "Consumer Discretionary": 0.20,  # max 20%
    "Communication":          0.15,  # max 15%
    "Energy":                 0.15,  # max 15%
}

# Sector descriptions — what drives each sector
SECTOR_DRIVERS = {
    "Financials": {
        "description": "Banks and financial services",
        "key_drivers":  ["interest rates", "credit growth",
                         "loan defaults", "regulatory changes"],
        "asx_stocks":   ["CBA.AX", "WBC.AX", "ANZ.AX", "MQG.AX"],
        "sp_stocks":    ["JPM", "BRK-B", "V"],
        "risk_level":   "Medium"
    },
    "Technology": {
        "description": "Software, hardware, semiconductors",
        "key_drivers":  ["AI growth", "cloud adoption",
                         "consumer spending", "interest rates"],
        "asx_stocks":   [],
        "sp_stocks":    ["AAPL", "MSFT", "GOOGL", "NVDA"],
        "risk_level":   "High"
    },
    "Materials": {
        "description": "Mining and raw materials",
        "key_drivers":  ["commodity prices", "China demand",
                         "AUD/USD", "iron ore price"],
        "asx_stocks":   ["BHP.AX", "RIO.AX", "FMG.AX"],
        "sp_stocks":    [],
        "risk_level":   "High"
    },
    "Healthcare": {
        "description": "Pharmaceuticals and biotech",
        "key_drivers":  ["drug approvals", "aging population",
                         "healthcare spending", "R&D pipeline"],
        "asx_stocks":   ["CSL.AX"],
        "sp_stocks":    ["JNJ"],
        "risk_level":   "Medium"
    },
    "Consumer Discretionary": {
        "description": "Retail and consumer goods",
        "key_drivers":  ["consumer confidence", "inflation",
                         "employment", "interest rates"],
        "asx_stocks":   ["WES.AX"],
        "sp_stocks":    ["AMZN"],
        "risk_level":   "Medium"
    },
    "Communication": {
        "description": "Telecom and media",
        "key_drivers":  ["subscriber growth", "5G rollout",
                         "competition", "infrastructure spend"],
        "asx_stocks":   ["TLS.AX"],
        "sp_stocks":    [],
        "risk_level":   "Low"
    },
    "Energy": {
        "description": "Oil, gas and energy",
        "key_drivers":  ["oil price", "OPEC decisions",
                         "renewable transition", "geopolitics"],
        "asx_stocks":   [],
        "sp_stocks":    ["XOM"],
        "risk_level":   "High"
    },
}

# Currency settings
CURRENCY_SETTINGS = {
    "AUD": {
        "symbol":    "A$",
        "benchmark": "^AXJO",   # ASX 200 index
    },
    "USD": {
        "symbol":    "$",
        "benchmark": "^GSPC",   # S&P 500 index
    }
}

# Portfolio construction rules
PORTFOLIO_RULES = {
    "max_single_stock":  0.15,  # no stock > 15% of portfolio
    "max_sector":        0.35,  # no sector > 35% of portfolio
    "min_stocks":        10,    # always hold at least 10 stocks
    "max_stocks":        20,    # maximum 20 stocks
    "rebalance_freq":    "monthly",
    "starting_capital":  100000,
}

if __name__ == "__main__":
    print("=" * 50)
    print("SECTOR CONFIGURATION")
    print("=" * 50)
    for sector, data in SECTOR_DRIVERS.items():
        print(f"\n{sector} (max {SECTOR_LIMITS[sector]*100:.0f}%)")
        print(f"  Risk:        {data['risk_level']}")
        print(f"  Key drivers: {', '.join(data['key_drivers'][:2])}")
        print(f"  ASX stocks:  {data['asx_stocks']}")
        print(f"  S&P stocks:  {data['sp_stocks']}")