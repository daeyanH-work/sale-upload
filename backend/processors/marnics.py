"""Processor for Marnics."""

from datetime import datetime


def process(df, selected_date: str) -> tuple:
    """
    Marnics: no content changes.

    The uploaded xlsx is passed through as-is; only the exported
    filename changes to 'Item Wise Sales Report MM-DD-YYYY.xlsx'.
    """
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        date_str = dt.strftime("%m-%d-%Y")
    except (ValueError, TypeError):
        date_str = selected_date

    output_filename = f"Item Wise Sales Report {date_str}.xlsx"
    return df, output_filename
