from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from .constants import MONTHS

STOCK_DATA_DIR = Path(__file__).parent.joinpath(Path("../data/stocks"))


@st.cache_data(ttl=60 * 60)
def load_stock_metadata() -> pd.DataFrame:
    all_files = list(STOCK_DATA_DIR.glob("*"))
    df_list = [pd.read_csv(file) for file in all_files]
    combined_df = pd.concat(df_list, ignore_index=True)

    return combined_df.rename(
        columns={
            "Symbol": "symbol",
            "Sector": "sector",
            "Company Name": "company_name",
            "Industry": "industry",
        }
    ).assign(symbol=lambda df_: df_["symbol"].add(".NS"))


@st.cache_data(ttl=60 * 60 * 24)
def download_closing_data(ticker: str) -> pd.Series:
    closing_data = yf.download(
        ticker,
        period="max",
        multi_level_index=False,
        auto_adjust=True,
    )["Close"]  # type: ignore

    return closing_data


def calc_annual_return(monthly_returns: pd.Series):
    return monthly_returns.add(1, fill_value=0.0).prod() - 1.0  # type: ignore


def add_monthly_contributions(df: pd.DataFrame):
    def get_monthly_contrib(monthly_series: pd.Series):
        return np.log1p(monthly_series[MONTHS]) / np.log1p(
            monthly_series["annual_returns"]
        )

    contrib = df.apply(get_monthly_contrib, axis=1).add_suffix("_contrib")
    return df.join(contrib)


def add_avg_monthly_return(df: pd.DataFrame):
    avg_monthly_returns = (
        df[MONTHS].mean(axis=0).rename("monthly_avg").to_frame().transpose()
    )
    return pd.concat([df, avg_monthly_returns])


@st.cache_data(ttl=60 * 60)
def get_monthly_analysis(
    ticker: str, stock_data: pd.Series | None = None
) -> pd.DataFrame:
    if stock_data is None:
        stock_data = download_closing_data(ticker)

    return (
        stock_data.to_frame("close")
        .resample("ME")
        .last()
        .assign(
            month=lambda df_: df_.index.strftime("%b"),  # type: ignore
            year=lambda df_: df_.index.strftime("%Y"),  # type: ignore
            monthly_returns=lambda df_: df_["close"].pct_change(),
        )
        .astype({"month": pd.CategoricalDtype(MONTHS, ordered=True)})
        .pivot_table(
            index="year", columns="month", values="monthly_returns", observed=True
        )
        .reindex(columns=MONTHS)
        .assign(
            annual_returns=lambda df_: df_.loc[:, "Jan":"Dec"].agg(
                calc_annual_return, axis=1
            ),
            first_half_avg=lambda df_: df_.loc[:, "Jan":"Jun"].mean(axis=1),
            second_half_avg=lambda df_: df_.loc[:, "Jul":"Dec"].mean(axis=1),
        )
        .pipe(add_monthly_contributions)
        .pipe(add_avg_monthly_return)
    )


def format_analysis(analysis: pd.DataFrame):
    return (
        analysis[
            [
                *MONTHS[:6],
                "first_half_avg",
                *MONTHS[6:],
                "second_half_avg",
                "annual_returns",
                *[f"{month}_contrib" for month in MONTHS],
            ]
        ]
        .rename(
            columns={
                "annual_returns": "Total Annual Returns",
                "first_half_avg": "Avg returns till June",
                "second_half_avg": "Avg returns after June",
                **{f"{month}_contrib": f"{month} Contribution" for month in MONTHS},
            },
            index={
                "monthly_avg": "Avg Monthly Returns",
            },
        )
        .mul(100)
        .round(2)
    )


if __name__ == "__main__":
    stock_df = load_stock_metadata()
    print(stock_df)
