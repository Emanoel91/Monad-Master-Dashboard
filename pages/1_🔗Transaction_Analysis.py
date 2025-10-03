# streamlit_flipside_app_requests.py
# Streamlit app that queries Flipside via direct HTTP request to MCP endpoint (without SDK) and shows an hourly tx_count bar chart.
# Usage:
# 1) Install requirements: pip install streamlit pandas altair requests
# 2) Add your API key in Streamlit Cloud → Settings → Secrets:
#    FLIPSIDE_API_KEY = "your_api_key_here"
# 3) Run: streamlit run streamlit_flipside_app_requests.py

import streamlit as st
import pandas as pd
import altair as alt
import requests
from datetime import timedelta

st.set_page_config(page_title="Flipside — Hourly TXs (Requests)", layout="wide")
st.title("نمودار ستونی تراکنش‌ها (ساعتی) — Flipside Data")

# --- Config / Inputs ---
api_key = st.secrets.get("FLIPSIDE_API_KEY")
if not api_key:
    st.error("کلید API پیدا نشد. لطفاً در Settings → Secrets کلید FLIPSIDE_API_KEY را وارد کنید.")
    st.stop()

days = st.sidebar.slider("روزهای گذشته برای نمایش", min_value=1, max_value=30, value=7)

sql = f"""
SELECT 
  date_trunc('hour', block_timestamp) as hour,
  count(distinct tx_hash) as tx_count
FROM ethereum.core.fact_transactions 
WHERE block_timestamp >= GETDATE() - interval '{days} days'
GROUP BY 1
ORDER BY 1
"""

endpoint_url = "https://mcp.flipsidecrypto.xyz/mcp/public/mcp"

@st.cache_data(ttl=timedelta(minutes=10))
def run_query(sql_text, api_key):
    headers = {"Content-Type": "application/json"}
    payload = {
        "sql": sql_text,
        "apiKey": api_key
    }
    try:
        response = requests.post(endpoint_url, json=payload, headers=headers, timeout=30)
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
        st.error(f"خطا در اجرای درخواست HTTP: {e}")
        return pd.DataFrame()

# --- Run and display ---
with st.spinner("در حال اجرای کوئری روی Flipside (Requests)..."):
    df = run_query(sql, api_key)

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
st.caption("تذکر: از کلید API در Secrets استفاده کنید تا امنیت حفظ شود.")
