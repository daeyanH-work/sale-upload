"""Processor for Global Communications."""

import pandas as pd


def process(df: pd.DataFrame, selected_date: str) -> pd.DataFrame:
    """
    Apply Global Communications–specific transformations.

    TODO: Replace the placeholder logic below with real business rules.
    """
    df = df.copy()
    df["Client"] = "Global Communications"
    df["Processed_Date"] = selected_date
    return df
