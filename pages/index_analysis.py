from calendar import month_name

import pandas as pd
import streamlit as st

from price_action_analysis.config import INDEX_CSV
from price_action_analysis.plots import generate_top_performers_barchart

st.set_page_config(layout="wide")


index_df = pd.read_csv(INDEX_CSV, engine="pyarrow", dtype_backend="pyarrow")
index_names = index_df["index"].unique().tolist()

selected_index = st.sidebar.selectbox("Choose an index:", index_names, index=1)

month_names = month_name[1:]
current_month = pd.Timestamp.now().month
selected_month_name = st.sidebar.selectbox(
    "Choose a month:", month_names, index=current_month - 1
)

st.title("Top Performers in Index")
st.write(f"### Selected Index: **{selected_index}**")
st.write(f"### Selected Month: **{selected_month_name}**")
month_num = month_names.index(selected_month_name) + 1

fig = generate_top_performers_barchart(selected_index, month_num)
st.plotly_chart(fig, use_container_width=True)
