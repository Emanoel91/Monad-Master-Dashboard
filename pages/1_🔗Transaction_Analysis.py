# streamlit_flipside_app_final.py
# Streamlit app that queries Flipside via Python SDK and shows hourly transaction counts.

from datetime import timedelta
import pandas as pd
import altair as alt
import streamlit as st

# Import Flipside SDK
try:
    from flipside import Flipside
except ImportError:
    st.error("SDK Flipside نصب نشده است. لطفاً pip install flipside-sdk را اجرا کنید.")
    st.stop()

st.set_page_config(page_title="Flipside — Hourly TXs", layout="wide")
st.title("نمودار ستونی تراکنش‌ها (ساعتی) — Flipside Data")

# --- Config / Inputs ---
api_key = st.secrets.get("FLIPSIDE_API_KEY")
api_url = "https://api-v2.flipsidecrypto.xyz"

if not api_key:
    st.error("کلید SDK API پیدا نشد. لطفاً در Settings → Secrets کلید FLIPSIDE_API_KEY را وارد کنید.")
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

@st.cache_data(ttl=timedelta(minutes=10))
def run_query(sql_text: str, key: str, url: str):
    client = Flipside(key, url)
    qrs = client.query(sql_text)

    try:
        if hasattr(qrs, "to_pandas"):
            df = qrs.to_pandas()
        else:
            df = pd.DataFrame(qrs)
    except Exception as e:
        st.error(f"خطا در تبدیل نتیجه به DataFrame: {e}")
        return pd.DataFrame()

    if 'hour' in df.columns:
        df['hour'] = pd.to_datetime(df['hour'])
    if 'tx_count' in df.columns:
        df['tx_count'] = pd.to_numeric(df['tx_count'], errors='coerce').fillna(0).astype(int)

    return df

# --- Run and display ---
with st.spinner("در حال اجرای کوئری روی Flipside (SDK)..."):
    df = run_query(sql, api_key, api_url)

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
st.caption("تذکر: از کلید SDK API در Secrets استفاده کنید تا امنیت حفظ شود.")
