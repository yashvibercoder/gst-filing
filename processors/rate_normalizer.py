"""
Rate Normalizer Module
Converts decimal rates (0.05, 0.12, 0.18) to whole numbers (5, 12, 18).
"""

import pandas as pd


def normalize_rate(df, rate_col):
    """
    Convert decimal rates to whole-number integers.
    - If rate <= 1: multiply by 100 (0.05 -> 5)
    - If rate > 1: keep as-is (already 5, 12, 18)
    - Cast to int
    """
    df = df.copy()
    rates = pd.to_numeric(df[rate_col], errors='coerce')
    mask = rates <= 1
    rates[mask] = rates[mask] * 100
    df[rate_col] = rates.astype(int)
    return df
