import streamlit as st

from src.loader import (
    format_analysis,
    get_monthly_analysis,
)
from src.plots import (
    generate_heatmap,
    generate_monthly_avg_barchart,
)

st.set_page_config(page_title="Price Action Dashboard", layout="wide")

# TODO: Add another sidebar for filtering based on sector

# TODO: Change the below code to show stock names of selected sector only

st.sidebar.title("Select Stock")
selected_stock_name = st.sidebar.selectbox("Choose a stock:", STOCK_NAMES)
selected_stock_ticker = STOCKS[selected_stock_name]

st.title("Price Action Dashboard")
st.write(f"### Selected Stock: **{selected_stock_ticker}**")

tab1, tab2, tab3 = st.tabs(["📄 Price Action Data", "🔥 Heatmap", "📊 Bar Charts"])


@st.cache_data(ttl=60 * 60)
def get_formatted_table(stock: str):
    return format_analysis(get_monthly_analysis(stock))


with tab1:
    st.subheader("Price Action DataFrame")
    analysis = get_formatted_table(selected_stock_ticker)
    st.dataframe(analysis)

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
