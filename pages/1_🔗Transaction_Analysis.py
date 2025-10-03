# streamlit_flipside_app.py
# Streamlit app that queries Flipside via their Python SDK and shows an hourly tx_count bar chart.
# Usage:
# 1) Install requirements: pip install streamlit flipside-sdk pandas altair
# 2) Add your API key in Streamlit Cloud → Settings → Secrets:
#    FLIPSIDE_API_KEY = "your_api_key_here"
# 3) Run: streamlit run streamlit_flipside_app.py

from datetime import timedelta
import pandas as pd
import altair as alt
import streamlit as st

# Try importing Flipside SDK
try:
    from flipside import Flipside
except Exception:
    Flipside = None

st.set_page_config(page_title="Flipside — Hourly TXs", layout="wide")
st.title("نمودار ستونی تراکنش‌ها (ساعتی) — Flipside Data")

# --- Config / Inputs ---
# Read API key from Streamlit secrets
api_key = st.secrets.get("FLIPSIDE_API_KEY")
api_url = "https://api-v2.flipsidecrypto.xyz"

if not api_key:
    st.error("کلید API پیدا نشد. لطفاً در Settings → Secrets کلید FLIPSIDE_API_KEY را وارد کنید.")
    st.stop()

# Simple query (same as the example you provided). You can edit time range in the UI.
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
    """Run the Flipside query and return a pandas DataFrame."""
    if Flipside is None:
        raise ImportError("Couldn't import `Flipside` from the flipside SDK. Make sure the package is installed and import path is correct.")

    client = Flipside(key, url)
    qrs = client.query(sql_text)

    df = None
    try:
        if hasattr(qrs, "to_pandas"):
            df = qrs.to_pandas()
    except Exception:
        df = None

    try:
        if df is None and isinstance(qrs, pd.DataFrame):
            df = qrs
    except Exception:
        pass

    if df is None:
        try:
            if isinstance(qrs, dict):
                if "results" in qrs:
                    df = pd.DataFrame(qrs["results"])
                elif "records" in qrs:
                    df = pd.DataFrame(qrs["records"])
        except Exception:
            df = None

    if df is None:
        try:
            df = pd.DataFrame(qrs)
        except Exception as e:
            raise RuntimeError(f"Unable to convert query result to DataFrame: {e}")

    if "hour" in df.columns:
        df["hour"] = pd.to_datetime(df["hour"])
    if "tx_count" in df.columns:
        df["tx_count"] = pd.to_numeric(df["tx_count"], errors="coerce").fillna(0).astype(int)

    return df

# --- Run and display ---
with st.spinner("در حال اجرای کوئری روی Flipside..."):
    try:
        df = run_query(sql, api_key, api_url)
    except Exception as e:
        st.error(f"اجرای کوئری ناموفق بود: {e}")
        st.stop()

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
st.caption("تذکر: کلید API را در Settings → Secrets در Streamlit Cloud قرار دهید تا امنیت حفظ شود.")
