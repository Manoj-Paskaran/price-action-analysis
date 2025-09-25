from calendar import month_name

import plotly.express as px

from .constants import MONTHS
from .data_loader import (
    add_avg_monthly_return,
    get_monthly_analysis,
    get_sector_monthly_analysis,
)
from .index_analyzer import get_top_performers


def generate_heatmap(
    ticker: str,
    min_year: int = 1900,
    max_year: int = 2100,
):
    monthly = (
        get_monthly_analysis(ticker)
        .filter(items=[str(y) for y in range(min_year, max_year + 1)], axis="index")
        .loc[:, MONTHS]
        .mul(100)
        .round(2)
    )

    fig = px.imshow(
        monthly,
        color_continuous_scale="RdYlGn",
        origin="upper",
        aspect="auto",
        text_auto=".2f",  # type: ignore
        labels=dict(month="Month", year="Year", color="Return (%)"),
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Year")
    fig.update_layout(
        title=f"Historical Monthly Returns of {ticker}",
        coloraxis_colorbar_ticksuffix="%",
    )
    return fig


def generate_monthly_avg_barchart(
    ticker: str, min_year: int = 1900, max_year: int = 2100
):
    res = (
        get_monthly_analysis(ticker)
        .filter(items=[str(y) for y in range(min_year, max_year + 1)], axis="index")
        .mul(100)
        .round(2)
        .pipe(add_avg_monthly_return)
        .loc["monthly_avg", MONTHS]
    )  # type: ignore

    fig = px.bar(
        x=res.index,
        y=res.values,
        labels={"x": "Month", "y": "Avg Monthly Returns (%)"},
        title=f"Average Monthly Returns for {ticker}",
        color=res.values,
        color_continuous_scale="RdYlGn",
        text=res.apply(lambda x: f"{x:.2f}%"),
    )
    return fig


def generate_sector_heatmap(
    sector: str,
    *,
    min_year: int = 1900,
    max_year: int = 2100,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> px.imshow:  # type: ignore
    sector_df = get_sector_monthly_analysis(
        sector,
        use_cache=use_cache,
        force_refresh=force_refresh,
    )

    filtered = (
        sector_df.filter(
            items=[str(y) for y in range(min_year, max_year + 1)], axis="index"
        )
        .mul(100)
        .round(2)
    )

    fig = px.imshow(
        filtered,
        color_continuous_scale="RdYlGn",
        origin="upper",
        aspect="auto",
        text_auto=".2f",  # type: ignore
        labels=dict(month="Month", year="Year", color="Return (%)"),
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Year")
    fig.update_layout(
        title=f"Sector Average Monthly Returns - {sector}",
        coloraxis_colorbar_ticksuffix="%",
    )
    return fig


def generate_sector_monthly_avg_barchart(
    sector: str,
    *,
    min_year: int = 1900,
    max_year: int = 2100,
    use_cache: bool = True,
    force_refresh: bool = False,
):
    sector_df = get_sector_monthly_analysis(
        sector, use_cache=use_cache, force_refresh=force_refresh
    )

    sector_df = sector_df.filter(
        items=[str(y) for y in range(min_year, max_year + 1)], axis="index"
    )
    sector_df = add_avg_monthly_return(sector_df)
    if "monthly_avg" not in sector_df.index:
        raise ValueError("Failed to compute monthly average for sector chart")

    monthly_avg = sector_df.loc[["monthly_avg"], MONTHS].iloc[0].mul(100).round(2)
    fig = px.bar(
        x=monthly_avg.index,
        y=monthly_avg.values,
        labels={"x": "Month", "y": "Avg Monthly Returns (%)"},
        title=f"Average Monthly Returns - Sector: {sector}",
        color=monthly_avg.values,
        color_continuous_scale="RdYlGn",
        text=[f"{v:.2f}%" for v in monthly_avg.values],
    )
    return fig


def generate_top_performers_barchart(
    index: str,
    month_num: int,
    min_year: int = 1900,
    max_year: int = 2100,
):
    top_performers = get_top_performers(
        index, month_num, min_year=min_year, max_year=max_year, index_df=None
    )

    fig = px.bar(
        top_performers,
        labels={"index": "Year", "value": "Number of times as Top Performer"},
        title=f"Top Performing Stocks in {month_name[month_num]} - Index: {index}",
        color=top_performers.values,
        color_continuous_scale="RdYlGn",
        text=top_performers.values,
    )
    return fig
