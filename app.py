import streamlit as st

st.set_page_config(
    page_title="Garmin Dashboard",
    page_icon="🏃",
    layout="wide",
)

# Custom CSS for minimal sidebar
st.markdown(
    """
    <style>
    /* Make sidebar more compact */
    [data-testid="stSidebar"] {
        min-width: 180px !important;
        max-width: 180px !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }
    /* Reduce padding in sidebar navigation */
    [data-testid="stSidebarNav"] {
        padding-top: 0.5rem;
    }
    [data-testid="stSidebarNav"] ul {
        padding-left: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

dashboard = st.Page("pages/dashboard.py", title="Dashboard", icon="🏠", default=True)
stream = st.Page("pages/stream.py", title="Stream", icon="📡")
settings = st.Page("pages/settings.py", title="Settings", icon="⚙️")

pg = st.navigation([dashboard, stream, settings])
pg.run()
