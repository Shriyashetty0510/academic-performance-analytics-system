from datetime import datetime
from utils.helpers import log_activity


# =====================================================
# INITIALIZE SESSION
# =====================================================

def initialize_session(st):
    """Initialize Streamlit session state variables."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "user" not in st.session_state:
        st.session_state.user = None

    if "last_activity" not in st.session_state:
        st.session_state.last_activity = None


# =====================================================
# SESSION TIMEOUT (10 minutes)
# =====================================================

def check_session_timeout(st):
    """Check if session expired (10 minutes inactivity)."""

    if "last_activity" not in st.session_state or st.session_state.last_activity is None:
        st.session_state.last_activity = datetime.now()
        return True

    elapsed = (datetime.now() - st.session_state.last_activity).seconds

    if elapsed > 600:  # 10 minutes
        st.warning("⚠️ Session expired. Please login again.")
        logout(st)
        st.rerun()
        return False

    st.session_state.last_activity = datetime.now()
    return True


# =====================================================
# LOGOUT
# =====================================================

def logout(st):
    """Logs out user and clears session."""

    if st.session_state.get("user"):
        log_activity(st.session_state.user["id"], "user_logout")

    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.last_activity = None
