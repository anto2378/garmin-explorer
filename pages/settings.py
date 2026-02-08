import shutil

import streamlit as st

from lib.cache import sync_user
from lib.database import (
    delete_user,
    get_activity_count,
    get_all_users,
    get_user_by_email,
)
from lib.garmin import (
    TOKENS_DIR,
    get_display_name,
    login,
    resume,
)

st.title("⚙️ Settings")
st.markdown("---")

# --- Connected users ---
st.subheader("Connected accounts")

# Get all users from database (handle migration gracefully)
try:
    db_users = {u["name"]: u for u in get_all_users()}
except Exception:
    # Database might not have garmin_email column yet
    db_users = {}

connected = []
if TOKENS_DIR.exists():
    connected = [
        d.name for d in sorted(TOKENS_DIR.iterdir()) if d.is_dir() and any(d.iterdir())
    ]

if connected:
    for name in connected:
        user_data = db_users.get(name, {})

        col1, col2, col3 = st.columns([3, 3, 1])

        # Name + email
        col1.markdown(f"**{name.title()}**")
        if user_data.get("garmin_email"):
            col1.caption(user_data["garmin_email"])

        # Status
        try:
            client = resume(name)
            display_name = get_display_name(client)
            cached = get_activity_count(name)
            col2.success(f"✅ {display_name} — {cached} activities")
        except Exception:
            col2.error("⚠️ Token expired")

        # Remove button
        if col3.button(
            "Remove",
            key=f"remove_{name}",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner(f"Removing {name}..."):
                try:
                    # Delete from database
                    delete_user(name)
                    # Delete token directory
                    token_dir = TOKENS_DIR / name
                    if token_dir.exists():
                        shutil.rmtree(token_dir)
                    st.success(f"✅ Removed {name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to remove {name}: {e}")
else:
    st.caption("No accounts connected yet.")

st.markdown("---")

# --- Add new account ---
st.subheader("Connect a Garmin account")

with st.form("garmin_login"):
    user_name = st.text_input(
        "Your name (short, lowercase — used as identifier)",
        placeholder="e.g. anto",
    )
    email = st.text_input("Garmin email", placeholder="you@example.com")
    password = st.text_input("Garmin password", type="password")
    submitted = st.form_submit_button("🔐 Connect", use_container_width=True)

if submitted:
    if not user_name or not email or not password:
        st.error("❌ All fields are required.")
    else:
        user_name = user_name.strip().lower().replace(" ", "_")
        email = email.strip().lower()

        # Check if email is already connected
        try:
            existing_user = get_user_by_email(email)
            if existing_user:
                st.warning(
                    f"⚠️ This Garmin account is already connected as **{existing_user['name'].title()}**. "
                    "Each Garmin account can only be connected once."
                )
                st.stop()
        except Exception:
            # Database might not have garmin_email column yet - skip check
            pass

        with st.spinner("Authenticating with Garmin..."):
            try:
                client = login(user_name, email, password)
                display_name = get_display_name(client)
                st.success(f"✅ Connected as **{display_name}**!")
            except Exception as e:
                error_msg = str(e).lower()

                # Provide user-friendly error messages
                if (
                    "authentication" in error_msg
                    or "login" in error_msg
                    or "credentials" in error_msg
                ):
                    st.error(
                        "❌ **Authentication failed** — Your email or password is incorrect. "
                        "Please double-check your Garmin credentials."
                    )
                elif (
                    "2fa" in error_msg
                    or "two-factor" in error_msg
                    or "mfa" in error_msg
                ):
                    st.error(
                        "❌ **Two-factor authentication detected** — This app doesn't support 2FA. "
                        "Please disable 2FA on your Garmin account or use a different account."
                    )
                elif (
                    "network" in error_msg
                    or "connection" in error_msg
                    or "timeout" in error_msg
                ):
                    st.error(
                        "❌ **Connection error** — Unable to reach Garmin servers. "
                        "Please check your internet connection and try again."
                    )
                elif (
                    "rate" in error_msg
                    or "limit" in error_msg
                    or "too many" in error_msg
                ):
                    st.error(
                        "❌ **Too many attempts** — Garmin has temporarily blocked login requests. "
                        "Please wait a few minutes and try again."
                    )
                else:
                    st.error(f"❌ **Connection failed** — {e}")
                    st.caption(
                        "Make sure your Garmin email and password are correct. "
                        "Note: Accounts with 2FA enabled are not supported."
                    )

                # Show full error stack in expander for debugging
                import traceback

                with st.expander("🔍 Debug details"):
                    st.code(traceback.format_exc(), language="python")

                st.stop()

        with st.spinner("Syncing activities (first time = last 90 days)..."):
            try:
                result = sync_user(user_name, garmin_email=email)
                st.success(
                    f"📥 **Synced {result['fetched']} activities** — "
                    f"{result['cached']} total cached"
                )
                st.balloons()
                st.rerun()
            except Exception as e:
                st.warning(f"⚠️ Authenticated successfully, but sync failed: {e}")
                st.info(
                    "Your account is connected. Try syncing again from the Stream page."
                )

                # Show full error stack for debugging
                import traceback

                with st.expander("🔍 Debug details"):
                    st.code(traceback.format_exc(), language="python")

                st.balloons()
                st.rerun()
