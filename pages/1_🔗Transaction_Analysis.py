# streamlit_flipside_mcp_test.py
# نسخه تست سریع برای بررسی اتصال MCP Key بدون خطای 401
# Usage:
# 1) Push این فایل به GitHub بدون کلید MCP
# 2) در Streamlit Cloud → Settings → Secrets:
#    FLIPSIDE_MCP_KEY = "کلید MCP واقعی شما"
# 3) اپ یک کوئری ساده اجرا می‌کند تا مطمئن شویم اتصال برقرار است

import streamlit as st
import requests
import pandas as pd

st.title("تست اتصال MCP Key — Streamlit")

# خواندن کلید از Secrets
mcp_key = st.secrets.get("FLIPSIDE_MCP_KEY")
if not mcp_key:
    st.error("کلید MCP پیدا نشد. لطفاً در Settings → Secrets کلید FLIPSIDE_MCP_KEY را وارد کنید.")
    st.stop()

# MCP endpoint URL
endpoint_url = f"https://mcp.flipsidecrypto.xyz/mcp/public/mcp?apiKey={mcp_key}"

# کوئری ساده برای تست: تعداد 1 تراکنش آخر Ethereum
sql_payload = {
    "sql": "SELECT tx_hash, block_timestamp FROM ethereum.core.fact_transactions ORDER BY block_timestamp DESC LIMIT 1"
}

try:
    response = requests.post(endpoint_url, json=sql_payload, timeout=20)
    response.raise_for_status()
    data = response.json()

    if 'results' in data:
        df = pd.DataFrame(data['results'])
    elif 'records' in data:
        df = pd.DataFrame(data['records'])
    else:
        df = pd.DataFrame(data)

    st.success("ارتباط برقرار شد! MCP Key معتبر است.")
    st.dataframe(df)

except requests.exceptions.HTTPError as e:
    st.error(f"خطا در اجرای درخواست MCP: {e}")
except requests.exceptions.RequestException as e:
    st.error(f"خطای شبکه یا اتصال: {e}")
