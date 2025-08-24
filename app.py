import io

import pandas as pd
import streamlit as st

from src.loader import (
    format_analysis,
    get_monthly_analysis,
    load_stock_metadata,
)
from src.plots import (
    generate_heatmap,
    generate_monthly_avg_barchart,
)

st.set_page_config(page_title="Price Action Dashboard", layout="wide")  # make page wide

stock_df = load_stock_metadata()

selected_sector = st.sidebar.selectbox(
    "Choose a sector:", sorted(stock_df["sector"].dropna().unique()), index=1
)
filtered_df = stock_df[stock_df["sector"] == selected_sector]

selected_stock_name = st.sidebar.selectbox(
    "Choose a stock:", filtered_df["company_name"]
)
selected_stock_ticker = filtered_df.loc[
    filtered_df["company_name"] == selected_stock_name, "symbol"
].values[0]  # type: ignore


st.title("Price Action Dashboard")
st.write(f"### Selected Stock: **{selected_stock_name}** `{selected_stock_ticker}`")

tab1, tab2, tab3 = st.tabs(["📄 Price Action Data", "🔥 Heatmap", "📊 Bar Chart"])


@st.cache_data(ttl=60 * 60)
def get_formatted_table(stock: str):
    return format_analysis(get_monthly_analysis(stock))


@st.cache_data
def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=True).encode("utf-8")


@st.cache_data
def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Analysis", index=True)
    return buf.getvalue()


with tab1:
    st.subheader("Price Action DataFrame")
    analysis = get_formatted_table(selected_stock_ticker)
    st.dataframe(analysis)

    st.download_button(
        "Download CSV",
        data=df_to_csv_bytes(analysis),
        file_name=f"{selected_stock_ticker}_analysis.csv",
        mime="text/csv",
        icon=":material/download:",
    )
    st.download_button(
        "Download Excel",
        data=df_to_excel_bytes(analysis),
        file_name=f"{selected_stock_ticker}_analysis.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        icon=":material/download:",
    )

with tab2:
    st.subheader("Heatmap")
    fig = generate_heatmap(selected_stock_ticker)
    fig.update_layout(
        height=600,
        font=dict(size=16),
    )
    st.plotly_chart(fig)

with tab3:
    st.subheader("Bar Chart")
    fig = generate_monthly_avg_barchart(selected_stock_ticker)
    st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": False})
