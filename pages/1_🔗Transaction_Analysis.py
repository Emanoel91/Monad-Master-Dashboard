from datetime import timedelta
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
