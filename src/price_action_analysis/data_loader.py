import asyncio
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from scipy import stats

from .config import SECTOR_DIR, STOCK_METADATA
from .constants import MONTHS


def get_cache_path_for_sector(sector: str) -> Path:
    SECTOR_DIR.mkdir(parents=True, exist_ok=True)
    safe_sector_name = re.sub(r"[^A-Za-z0-9_-]+", "_", sector.strip())

    return SECTOR_DIR / f"{safe_sector_name}.parquet"


def load_stock_metadata() -> pd.DataFrame:
    return pd.read_parquet(STOCK_METADATA, engine="pyarrow", dtype_backend="pyarrow")


def download_closing_data(ticker: str) -> pd.Series:
    closing_data = yf.download(
        ticker,
        period="max",
        multi_level_index=False,
        auto_adjust=True,
        progress=False,
    )["Close"]  # type: ignore

    return closing_data


def calc_annual_return(monthly_returns: pd.Series):
    return monthly_returns.add(1, fill_value=0.0).prod() - 1.0  # type: ignore


def add_avg_monthly_return(df: pd.DataFrame):
    avg_monthly_returns = (
        df[MONTHS].mean(axis=0).rename("monthly_avg").to_frame().transpose()
    )
    return pd.concat([df, avg_monthly_returns])


def get_monthly_analysis(
    ticker: str,
    stock_data: pd.Series | None = None,
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
    )


def get_sector_monthly_analysis(
    sector: str,
    stock_df: pd.DataFrame | None = None,
    use_cache: bool = True,
    force_refresh: bool = False,
    max_concurrency: int = 8,
) -> pd.DataFrame:  # type: ignore
    if stock_df is None:
        stock_df = load_stock_metadata()

    cache_path = get_cache_path_for_sector(sector)

    if use_cache and not force_refresh and cache_path.exists():
        try:
            return pd.read_parquet(cache_path, engine="pyarrow")
        except Exception:
            try:
                cache_path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:
                pass

    tickers = (
        stock_df.loc[stock_df["sector"] == sector, "symbol"].dropna().unique().tolist()
    )

    if not tickers:
        raise ValueError(f"No symbols found for sector '{sector}'")

    async def _fetch(ticker: str):
        try:
            analysis = await asyncio.to_thread(get_monthly_analysis, ticker)
            if analysis is None or analysis.empty:
                return None
            return ticker, analysis[MONTHS]

        except Exception:
            return None

    async def _gather():
        sem = asyncio.Semaphore(max_concurrency)

        async def _bounded(ticker: str):
            async with sem:
                return await _fetch(ticker)

        tasks = [asyncio.create_task(_bounded(s)) for s in tickers]
        return await asyncio.gather(*tasks)

    try:
        results = asyncio.run(_gather())
    except RuntimeError:
        # Fallback to iterative solution for environments with existing event loop
        results = []
        for ticker in tickers:
            try:
                analysis = get_monthly_analysis(ticker)
                if analysis is not None and not analysis.empty:
                    results.append((ticker, analysis[MONTHS]))
            except Exception:
                continue

    stock_monthly_results: list[pd.DataFrame] = []
    retrieved_tickers: list[str] = []
    for r in results:  # type: ignore
        if not r:
            continue
        ticker, analysis = r
        stock_monthly_results.append(analysis)
        retrieved_tickers.append(ticker)

    if not stock_monthly_results:
        raise ValueError(f"Unable to build monthly data for sector '{sector}'")

    combined = pd.concat(
        stock_monthly_results, keys=retrieved_tickers, names=["symbol", "year"]
    )  # type: ignore[arg-type]
    sector_monthly = combined.groupby("year").mean(numeric_only=True)
    result = sector_monthly.reindex(columns=MONTHS)

    # Write cache
    if use_cache:
        try:
            result.to_parquet(cache_path, engine="pyarrow")
        except Exception:
            pass

    return result


def force_rewrite_all_sector_caches(
    stock_df: pd.DataFrame | None = None,
):
    if stock_df is None:
        stock_df = load_stock_metadata()

    sectors_series = stock_df.get("sector")

    sectors = sectors_series.dropna().astype(str).str.strip()  # type: ignore
    sectors = sectors[sectors != ""].unique().tolist()

    status: dict[str, str] = {}
    for sector in sorted(sectors):
        try:
            _ = get_sector_monthly_analysis(
                sector,
                stock_df=stock_df,
                use_cache=False,
                force_refresh=True,
            )
            status[sector] = "ok"
        except Exception as e:
            status[sector] = f"error: {e}"

    return status


@st.cache_data(ttl=60 * 60)
def get_formatted_table(analysis: pd.DataFrame):
    return (
        analysis.assign(
            annual_returns=lambda df_: df_.loc[:, "Jan":"Dec"].agg(
                calc_annual_return, axis=1
            ),
            first_half_avg=lambda df_: df_.loc[:, "Jan":"Jun"].mean(axis=1),
            second_half_avg=lambda df_: df_.loc[:, "Jul":"Dec"].mean(axis=1),
        )[
            [
                *MONTHS[:6],
                "first_half_avg",
                *MONTHS[6:],
                "second_half_avg",
                "annual_returns",
            ]
        ]
        .pipe(add_avg_monthly_return)
        .rename(
            columns={
                "annual_returns": "Total Annual Returns",
                "first_half_avg": "Avg returns till June",
                "second_half_avg": "Avg returns after June",
            },
            index={
                "monthly_avg": "Avg Monthly Returns",
            },
        )
        .mul(100)
        .round(2)
    )


# hypothesis testing for each month
def monthly_hypothesis_results(returns_df):
    # returns_df: df with years as rows, months as columns, monthly returns as values
    results = {}
    months = [
        col
        for col in returns_df.columns
        if col not in ["annual_returns", "first_half_avg", "second_half_avg"]
    ]

    for month in months:
        data = returns_df[month].dropna().values
        if len(data) == 0:
            results[month] = "No Data"
            continue

        # calculated one-sample t-test against 0
        t_stat, p_val = stats.ttest_1samp(data, 0.0)
        mean = np.mean(data)
        # Checking significance at 95% CI
        if p_val < 0.05:  # type: ignore
            if mean > 0:
                results[month] = "Up"
            else:
                results[month] = "Down"
        else:
            results[month] = "Cannot Conclude @95% CI"
    return results


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=True).encode("utf-8")


def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Analysis", index=True)
    return buf.getvalue()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        sys.exit(0)

    if sys.argv[1] == "reload-sector-cache":
        status = force_rewrite_all_sector_caches()
        for sector, stat in status.items():
            print(f"{sector}: {stat}")
        sys.exit(0)
