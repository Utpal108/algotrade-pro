import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from transformers import pipeline
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

# ── Load FinBERT ─────────────────────────────────────────────
# FinBERT is a BERT model trained specifically on financial text
# First run will download the model (~500MB) — be patient
print("Loading FinBERT model...")
print("(First time takes 2-3 minutes to download)")

finbert = pipeline(
    "text-classification",
    model="ProsusAI/finbert",
    tokenizer="ProsusAI/finbert"
)

print("✅ FinBERT loaded successfully")

# ── Pull Real Apple News ─────────────────────────────────────
print("\nFetching Apple news headlines...")
stock = yf.Ticker("AAPL")
news  = stock.news

headlines = []
for article in news[:20]:  # get latest 20 articles
    title = article.get("content", {}).get("title", "")
    if title:
        headlines.append(title)

print(f"✅ Found {len(headlines)} headlines")
print("\nSample headlines:")
for h in headlines[:5]:
    print(f"  - {h}")

# ── Run BERT Sentiment Analysis ──────────────────────────────
print("\nAnalyzing sentiment with FinBERT...")

results = []
for headline in headlines:
    try:
        result = finbert(headline[:512])[0]  # max 512 tokens for BERT
        results.append({
            "headline":  headline,
            "sentiment": result["label"],
            "confidence": result["score"]
        })
    except Exception as e:
        print(f"Skipping headline: {e}")

df_sentiment = pd.DataFrame(results)

print("\n===== SENTIMENT RESULTS =====")
print(df_sentiment[["headline", "sentiment", "confidence"]].to_string())

# ── Aggregate Sentiment Score ────────────────────────────────
sentiment_counts = df_sentiment["sentiment"].value_counts()
total            = len(df_sentiment)

positive = sentiment_counts.get("positive", 0)
negative = sentiment_counts.get("negative", 0)
neutral  = sentiment_counts.get("neutral", 0)

# Calculate composite sentiment score (-1 to +1)
sentiment_score = (positive - negative) / total

print("\n===== SENTIMENT SUMMARY =====")
print(f"Positive: {positive} ({positive/total*100:.1f}%)")
print(f"Negative: {negative} ({negative/total*100:.1f}%)")
print(f"Neutral:  {neutral}  ({neutral/total*100:.1f}%)")
print(f"Composite Score: {sentiment_score:.3f}")

if sentiment_score > 0.3:
    bert_signal = "STRONG POSITIVE — Bullish"
elif sentiment_score > 0.1:
    bert_signal = "POSITIVE — Mildly Bullish"
elif sentiment_score > -0.1:
    bert_signal = "NEUTRAL — No clear direction"
elif sentiment_score > -0.3:
    bert_signal = "NEGATIVE — Mildly Bearish"
else:
    bert_signal = "STRONG NEGATIVE — Bearish"

print(f"BERT Signal: {bert_signal}")

# ── Save results ─────────────────────────────────────────────
df_sentiment.to_csv("data/AAPL_sentiment.csv", index=False)
print("\n✅ Sentiment data saved to data/AAPL_sentiment.csv")

# ── Chart ────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("AAPL — FinBERT Sentiment Analysis", fontsize=14)

# Chart 1: Sentiment distribution pie chart
colors = ["lime", "red", "gray"]
sizes  = [positive, negative, neutral]
labels = [f"Positive\n{positive}", f"Negative\n{negative}", f"Neutral\n{neutral}"]

axes[0].pie(sizes, labels=labels, colors=colors,
            autopct="%1.1f%%", startangle=90)
axes[0].set_facecolor("#1a1a2e")
axes[0].set_title("Sentiment Distribution")

# Chart 2: Confidence scores per headline
colors_bar = ["lime" if s == "positive" else
              "red"  if s == "negative" else
              "gray" for s in df_sentiment["sentiment"]]

short_labels = [h[:30] + "..." for h in df_sentiment["headline"]]
axes[1].barh(short_labels, df_sentiment["confidence"],
             color=colors_bar, alpha=0.8)
axes[1].set_facecolor("#1a1a2e")
axes[1].set_title("Confidence Score per Headline")
axes[1].set_xlabel("Confidence")
axes[1].grid(True, alpha=0.3)

fig.patch.set_facecolor("#0f0f23")
plt.tight_layout()
plt.savefig("data/AAPL_sentiment_analysis.png", dpi=150, bbox_inches="tight")
plt.show()
print("✅ Sentiment chart saved")