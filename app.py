import streamlit as st

st.set_page_config(
    page_title="Garmin Dashboard",
    page_icon="🏃",
    layout="wide",
)

dashboard = st.Page("pages/dashboard.py", title="Dashboard", icon="🏠", default=True)
stream = st.Page("pages/stream.py", title="Stream", icon="📡")
settings = st.Page("pages/settings.py", title="Settings", icon="⚙️")

pg = st.navigation({"Garmin Dashboard": [dashboard, stream, settings]})
pg.run()
