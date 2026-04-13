"""Processor for Cherry Berry."""

import pandas as pd


def process(df: pd.DataFrame, selected_date: str) -> pd.DataFrame:
    """
    Apply Cherry Berry–specific transformations.

    TODO: Replace the placeholder logic below with real business rules.
    """
    df = df.copy()
    df["Client"] = "Cherry Berry"
    df["Processed_Date"] = selected_date
    return df
