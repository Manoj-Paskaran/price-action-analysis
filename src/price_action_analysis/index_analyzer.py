import pandas as pd
import yfinance as yf

from .config import INDEX_CSV


def get_top_performers(
    index: str,
    month_num: int,
    min_year=1900,
    max_year=2100,
    index_df: pd.DataFrame | None = None,
) -> pd.Series:
    if index_df is None:
        index_df = pd.read_csv(INDEX_CSV, engine="pyarrow", dtype_backend="pyarrow")

    stocks = index_df[index_df["index"] == index]["ticker"].to_list()
    stocks_df = yf.download(
        stocks,
        period="max",
        auto_adjust=True,
        progress=False,
    )["Close"]  # type: ignore

    top_performers = (
        stocks_df.resample("ME")
        .last()
        .pct_change()
        .query(
            "index.dt.month == @month_num & (index.dt.year >= @min_year & index.dt.year <= @max_year)"
        )  # type: ignore
        .idxmax(axis=1)
        .value_counts()
    )

    return top_performers
