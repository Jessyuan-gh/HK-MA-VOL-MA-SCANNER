import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="港股通 MA + 大成交選股", layout="centered")

st.title("📈 港股通 MA + 大成交訊號")

if os.path.exists("last_update.txt"):
    with open("last_update.txt", "r") as f:
        update_time = f.read().strip()
    st.caption(f"最後更新時間 (HKT)：{update_time}（每日收市後自動更新）")

if os.path.exists("results.csv"):
    try:
        df = pd.read_csv("results.csv", dtype={"代號": str})
        st.metric(label="今日符合條件股票數量", value=len(df))
        
        if len(df) > 0:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("今日暫時未有港股通股票同時符合「企穩 MA20/50 + 1.5倍大成交」條件。")
    except pd.errors.EmptyDataError:
        st.metric(label="今日符合條件股票數量", value=0)
        st.info("今日暫時未有股票符合條件。")
else:
    st.warning("尚未執行第一次數據掃描，請先在 GitHub Actions 運行一次。")
