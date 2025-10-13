import asyncio

import streamlit as st

from price_action_analysis.config import NIFTY_50_CSV
from price_action_analysis.data_loader import get_index_heatmap_data
from price_action_analysis.plots import generate_stock_treemap

st.set_page_config(layout="wide")

st.title("Nifty 50 Stock Heatmap")
with st.spinner("Loading data..."):
    @st.cache_data
    def load_index_stock_data(csv_path):
        return asyncio.run(get_index_heatmap_data(csv_path))

    index_stock_data = load_index_stock_data(NIFTY_50_CSV)

fig = generate_stock_treemap(index_stock_data)
st.plotly_chart(fig, use_container_width=True)
