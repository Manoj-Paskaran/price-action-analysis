import pandas as pd
import plotly.express as px

from .constants import MONTHS
from .loader import (
    download_closing_data,
    get_monthly_analysis,
)


def generate_heatmap(ticker: str, closing_data: pd.Series | None = None):
    if closing_data is None:
        closing_data = download_closing_data(ticker)

    res = (
        closing_data.to_frame("close")
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
        .mul(100)
        .round(2)
    )

    fig = px.imshow(
        res,
        color_continuous_scale="RdYlGn",
        origin="upper",
        aspect="auto",
        text_auto=".2f",
        labels=dict(month="Month", year="Year", color="Return (%)"),
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Year")
    fig.update_layout(
        title=f"Historical Monthly Returns of {ticker}",
        coloraxis_colorbar_ticksuffix="%",
    )
    return fig


def generate_monthly_avg_barchart(ticker: str, closing_data: pd.Series | None = None):
    if closing_data is None:
        closing_data = download_closing_data(ticker)

    res = (
        get_monthly_analysis(ticker, closing_data)
        .mul(100)
        .round(2)
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
    # fig.update_layout(yaxis_tickformat=".02%")
    return fig


