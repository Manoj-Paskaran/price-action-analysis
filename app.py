from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from price_action_analysis.data_loader import (
    df_to_csv_bytes,
    df_to_excel_bytes,
    get_cache_path_for_sector,
    get_formatted_table,
    get_monthly_analysis,
    get_sector_monthly_analysis,
    load_stock_metadata,
    monthly_hypothesis_results,
)
from price_action_analysis.plots import (
    generate_heatmap,
    generate_monthly_avg_barchart,
    generate_sector_heatmap,
    generate_sector_monthly_avg_barchart,
)

st.set_page_config(page_title="Price Action Dashboard", layout="wide")

stock_df = load_stock_metadata()

sector_names = sorted(stock_df["sector"].dropna().unique().tolist())
sector_names.insert(0, "All Sectors")

selected_sector = st.sidebar.selectbox("Choose a sector:", sector_names, index=1)

if selected_sector == "All Sectors":
    sector_df = stock_df
elif selected_sector != "All Sectors":
    sector_df = stock_df.query("sector == @selected_sector")

stock_names = sector_df["company_name"].tolist()

if selected_sector != "All Sectors":
    stock_names.insert(0, "Entire Sector")

selected_stock_name = st.sidebar.selectbox("Choose a stock:", stock_names, index=0)

st.title("Price Action Dashboard")

selected_ticker: str
if selected_stock_name == "Entire Sector":
    selected_ticker = "SECTOR"  # type: ignore
    st.write(f"### Selected Sector: **{selected_sector}**")
else:
    selected_ticker = sector_df.set_index("company_name")["symbol"].get(
        selected_stock_name
    )  # type: ignore
    st.write(f"### Selected Stock: **{selected_stock_name}** `{selected_ticker}`")


if selected_ticker == "SECTOR":
    cache_caption = st.empty()
    force_refresh = False  # will render at bottom

    cache_path = get_cache_path_for_sector(str(selected_sector))  # type: ignore

    def _format_age(delta_seconds: float) -> str:
        if delta_seconds < 60:
            return "just now"
        if delta_seconds < 3600:
            mins = int(delta_seconds // 60)
            return f"{mins} min{'s' if mins != 1 else ''} ago"
        if delta_seconds < 86400:
            hours = delta_seconds / 3600
            return f"{hours:.1f} h ago"
        days = delta_seconds / 86400
        return f"{days:.1f} d ago"

    if cache_path.exists():
        age = datetime.now(timezone.utc).timestamp() - cache_path.stat().st_mtime
        cache_caption.caption(f"Last updated: {_format_age(age)}")
    else:
        cache_caption.caption("No cached sector data yet.")

    with st.spinner("Loading sector analysis (cached if available)..."):
        assert isinstance(selected_sector, str)
        data = get_sector_monthly_analysis(
            selected_sector, stock_df=stock_df, force_refresh=False
        )

    if cache_path.exists():
        age = datetime.now(timezone.utc).timestamp() - cache_path.stat().st_mtime
        cache_caption.caption(f"Last updated: {_format_age(age)}")

elif selected_ticker != "SECTOR":
    data = get_monthly_analysis(selected_ticker)  # type: ignore

min_year, max_year = data.index.min(), data.index.max()

if min_year != max_year:
    st.write(f"Data available from **{min_year}** to **{max_year}**")
    selected_min_year, selected_max_year = st.slider(
        label="Select Year Range",
        min_value=int(min_year),
        max_value=int(max_year),
        value=(int(min_year), int(max_year)),
        step=1,
    )

elif min_year == max_year:
    selected_min_year = selected_max_year = int(min_year)
    st.write(f"**Data available for year :** {min_year}")


data = data.filter(
    items=[str(y) for y in range(selected_min_year, selected_max_year + 1)], axis=0
)
tab1, tab2, tab3, tab4 = st.tabs(
    ["📄 Price Action Data", "🔥 Heatmap", "📊 Bar Chart", "📊 Stat Test"]
)

with tab1:
    st.subheader("Price Action DataFrame")
    formatted_table = get_formatted_table(data)
    st.dataframe(formatted_table)

    col1, col2 = st.columns([1, 5])
    with col1:
        st.download_button(
            "Download CSV",
            data=df_to_csv_bytes(formatted_table),
            file_name=f"{selected_ticker}_analysis.csv",
            mime="text/csv",
            icon=":material/download:",
            key="dl_csv",
        )
    with col2:
        st.download_button(
            "Download Excel",
            data=df_to_excel_bytes(formatted_table),
            file_name=f"{selected_ticker}_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            icon=":material/download:",
            key="dl_xlsx",
        )

with tab2:
    st.subheader("Heatmap")
    if selected_ticker == "SECTOR":
        fig = generate_sector_heatmap(
            selected_sector,  # type: ignore[arg-type]
            min_year=selected_min_year,
            max_year=selected_max_year,
        )
    else:
        fig = generate_heatmap(
            selected_ticker,
            min_year=selected_min_year,
            max_year=selected_max_year,
        )
    fig.update_layout(
        height=600,
        font=dict(size=20),
    )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})

with tab3:
    st.subheader("Bar Chart")
    if selected_ticker == "SECTOR":
        fig = generate_sector_monthly_avg_barchart(
            selected_sector,  # type: ignore[arg-type]
            min_year=selected_min_year,
            max_year=selected_max_year,
        )
    else:
        fig = generate_monthly_avg_barchart(
            selected_ticker,
            min_year=selected_min_year,
            max_year=selected_max_year,
        )
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})

with tab4:
    st.subheader("Monthly Hypothesis Testing at 95% Confidence Interval")

    results_dict = monthly_hypothesis_results(data)
    results_df = pd.DataFrame(
        list(results_dict.items()), columns=["Month", "Hypothesis Test Result"]
    )
    st.dataframe(results_df)

if selected_ticker == "SECTOR":
    st.divider()
    force_refresh_bottom = st.button("Force Refresh Sector Cache", type="primary")
    if force_refresh_bottom:
        with st.spinner("Refreshing sector cache..."):
            data = get_sector_monthly_analysis(selected_sector, force_refresh=True)  # type: ignore[arg-type]

        cache_path = get_cache_path_for_sector(str(selected_sector))
        if cache_path.exists():
            age = datetime.now(timezone.utc).timestamp() - cache_path.stat().st_mtime
            cache_caption.caption(f"Last updated: {_format_age(age)} (just refreshed)")
