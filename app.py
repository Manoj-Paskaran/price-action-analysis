import streamlit as st

monthly_analysis_page = st.Page("pages/monthly_analysis.py", title="Monthly Analysis", default=True)
index_analysis_page = st.Page("pages/index_analysis.py", title="Index Analysis")
stock_heatmap_page = st.Page("pages/stock_heatmap.py", title="Stock Heatmap")

pg = st.navigation([monthly_analysis_page, index_analysis_page, stock_heatmap_page])
pg.run()