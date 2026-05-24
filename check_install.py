import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ta
import sklearn
import torch
import transformers
import streamlit
import backtrader

print("yfinance:", yf.__version__)
print("pandas:", pd.__version__)
print("numpy:", np.__version__)
print("ta: installed")
print("scikit-learn:", sklearn.__version__)
print("torch:", torch.__version__)
print("transformers:", transformers.__version__)
print("streamlit:", streamlit.__version__)
print("backtrader: installed")
print("\n✅ All libraries loaded successfully")