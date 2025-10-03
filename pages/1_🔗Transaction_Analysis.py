# streamlit_flipside_mcp_github_ready.py
# نسخه آماده برای GitHub: استفاده از MCP Key از Streamlit Secrets بدون افشای کلید
# Usage:
# 1) Push این فایل به GitHub بدون کلید MCP
# 2) در Streamlit Cloud → Settings → Secrets:
#    FLIPSIDE_MCP_KEY = "کلید MCP واقعی شما"
# 3) اپ به صورت خودکار کلید را از Secrets می‌خواند و نمودار را نمایش می‌دهد

import streamlit as st
import pandas as pd
import altair as alt
import requests
from datetime import timedelta

st.set_page_config(page_title="Flipside MCP — Hourly TXs", layout="wide")
st.title("نمودار ستونی تراکنش‌ها (ساعتی) — Flipside MCP")

# --- خواندن کلید از Secrets ---
mcp_key = st.secrets.get("FLIPSIDE_MCP_KEY")
if not mcp_key:
    st.error("کلید MCP پیدا نشد. لطفاً در Settings → Secrets کلید FLIPSIDE_MCP_KEY را وارد کنید.")
    st.stop()

# --- پارامترهای کاربر ---
days = st.sidebar.slider("روزهای گذشته برای نمایش", min_value=1, max_value=30, value=7)

# MCP endpoint URL
endpoint_url = f"https://mcp.flipsidecrypto.xyz/mcp/public/mcp?apiKey={mcp_key}"

# SQL query payload
sql_payload = {
    "sql": f"""
    SELECT 
      date_trunc('hour', block_timestamp) as hour,
      count(distinct tx_hash) as tx_count
    FROM ethereum.core.fact_transactions 
    WHERE block_timestamp >= GETDATE() - interval '{days} days'
    GROUP BY 1
    ORDER BY 1
    """
}

@st.cache_data(ttl=timedelta(minutes=10))
def run_query(payload):
    try:
        response = requests.post(endpoint_url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if 'results' in data:
            df = pd.DataFrame(data['results'])
        elif 'records' in data:
            df = pd.DataFrame(data['records'])
        else:
            df = pd.DataFrame(data)

        if 'hour' in df.columns:
            df['hour'] = pd.to_datetime(df['hour'])
        if 'tx_count' in df.columns:
            df['tx_count'] = pd.to_numeric(df['tx_count'], errors='coerce').fillna(0).astype(int)

        return df

    except requests.exceptions.RequestException as e:
        st.error(f"خطا در اجرای درخواست MCP: {e}")
        return pd.DataFrame()

# --- اجرای کوئری و نمایش ---
with st.spinner("در حال اجرای کوئری روی Flipside MCP..."):
    df = run_query(sql_payload)

st.subheader(f"تعداد تراکنش‌ها - هر ساعت در {days} روز گذشته")

if df.empty:
    st.info("نتیجه‌ای برای نمایش وجود ندارد.")
else:
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("hour:T", title="ساعت", axis=alt.Axis(format="%Y-%m-%d %H:%M")),
        y=alt.Y("tx_count:Q", title="تعداد تراکنش‌های یکتا"),
        tooltip=[alt.Tooltip("hour:T", title="ساعت"), alt.Tooltip("tx_count:Q", title="تعداد تراکنش")]
    ).properties(height=500, width="container")

    st.altair_chart(chart, use_container_width=True)

    if st.checkbox("نمایش جدول داده‌ها"):
        st.dataframe(df)

st.markdown("---")
st.caption("تذکر: از کلید MCP در Secrets استفاده کنید تا امنیت حفظ شود.")
