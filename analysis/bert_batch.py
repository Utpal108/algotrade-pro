import pandas as pd
import warnings
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
from universe.stocks import ALL_TICKERS, ALL_STOCKS
warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════
# BATCH BERT SENTIMENT ANALYSIS
# Runs every morning — analyzes all 20 stocks
# Saves results to data/bert_scores.csv
# ════════════════════════════════════════════════════════════

def load_finbert():
    """Load FinBERT model once and reuse"""
    print("Loading FinBERT model...")
    from transformers import pipeline
    finbert = pipeline(
        "text-classification",
        model="ProsusAI/finbert",
        tokenizer="ProsusAI/finbert"
    )
    print("✅ FinBERT loaded")
    return finbert

def analyze_stock_sentiment(ticker, finbert):
    """
    Analyze sentiment for a single stock
    Returns score 0-100 and signal
    """
    import yfinance as yf

    try:
        stock     = yf.Ticker(ticker)
        news      = stock.news
        headlines = []

        for article in news[:15]:
            title = article.get(
                "content", {}).get("title", "")
            if title:
                headlines.append(title)

        if not headlines:
            return {
                "ticker":           ticker,
                "bert_score":       50,
                "positive":         0,
                "negative":         0,
                "neutral":          0,
                "total_headlines":  0,
                "signal":           "NEUTRAL",
                "top_headline":     "No headlines found"
            }

        positive = negative = neutral = 0
        top_headline = headlines[0]

        for headline in headlines:
            try:
                result = finbert(headline[:512])[0]
                if result["label"] == "positive":
                    positive += 1
                elif result["label"] == "negative":
                    negative += 1
                else:
                    neutral  += 1
            except:
                pass

        total          = positive + negative + neutral
        sentiment_score= (positive - negative) / total \
                          if total > 0 else 0
        bert_score     = int((sentiment_score + 1) / 2 * 100)

        if sentiment_score > 0.3:
            signal = "STRONG POSITIVE"
        elif sentiment_score > 0.1:
            signal = "POSITIVE"
        elif sentiment_score > -0.1:
            signal = "NEUTRAL"
        elif sentiment_score > -0.3:
            signal = "NEGATIVE"
        else:
            signal = "STRONG NEGATIVE"

        return {
            "ticker":          ticker,
            "bert_score":      bert_score,
            "positive":        positive,
            "negative":        negative,
            "neutral":         neutral,
            "total_headlines": total,
            "signal":          signal,
            "top_headline":    top_headline[:100]
        }

    except Exception as e:
        print(f"   ❌ Error for {ticker}: {e}")
        return {
            "ticker":          ticker,
            "bert_score":      50,
            "positive":        0,
            "negative":        0,
            "neutral":         0,
            "total_headlines": 0,
            "signal":          "NEUTRAL",
            "top_headline":    "Error fetching news"
        }

def run_batch_bert():
    """Run BERT on all 20 stocks and save results"""
    print("=" * 60)
    print("BATCH BERT SENTIMENT ANALYSIS")
    print("All 20 stocks")
    print("=" * 60)

    # Load model once
    finbert = load_finbert()

    results = []
    for i, ticker in enumerate(ALL_TICKERS):
        name = ALL_STOCKS[ticker]["name"]
        print(f"\n[{i+1}/20] Analyzing {ticker} ({name})...")
        result = analyze_stock_sentiment(ticker, finbert)
        results.append(result)
        print(f"   Score: {result['bert_score']}/100 "
              f"| Signal: {result['signal']}")
        print(f"   +{result['positive']} "
              f"-{result['negative']} "
              f"~{result['neutral']} "
              f"({result['total_headlines']} headlines)")

    # Save results
    df = pd.DataFrame(results)
    df.to_csv("data/bert_scores.csv", index=False)

    # Print summary
    print("\n" + "=" * 60)
    print("BERT SENTIMENT SUMMARY")
    print("=" * 60)
    print(f"\n{'Ticker':<8} {'Score':>6} {'Signal':<20} "
          f"{'Headlines':<10}")
    print("-" * 50)

    df_sorted = df.sort_values("bert_score", ascending=False)
    for _, row in df_sorted.iterrows():
        emoji = ("🟢" if row["bert_score"] >= 60
                 else "🔴" if row["bert_score"] < 40
                 else "⚪")
        print(f"{row['ticker']:<8} "
              f"{row['bert_score']:>5}/100 "
              f"{emoji} {row['signal']:<18} "
              f"{row['total_headlines']} headlines")

    print(f"\n✅ BERT scores saved to data/bert_scores.csv")
    print(f"   Average sentiment score: "
          f"{df['bert_score'].mean():.1f}/100")
    print(f"   Most positive: "
          f"{df.loc[df['bert_score'].idxmax(), 'ticker']}")
    print(f"   Most negative: "
          f"{df.loc[df['bert_score'].idxmin(), 'ticker']}")

    return df

if __name__ == "__main__":
    run_batch_bert()