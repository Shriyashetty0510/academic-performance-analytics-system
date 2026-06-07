import streamlit as st
from datetime import datetime

from auth.auth_service import authenticate_user, register_user
from utils.helpers import validate_email


# ============================================
# LOGIN PAGE
# ============================================

def login_page():
    """Display login and registration page"""
    st.title("🎓 APAS - Academic Performance Analytics System")

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    # ---------------------------
    # LOGIN TAB
    # ---------------------------
    with tab1:
        email = st.text_input("📧 Email", key="login_email")
        password = st.text_input("🔒 Password", type="password", key="login_password")

        if st.button("🚀 Login", use_container_width=True):
            if email.strip() == "" or password.strip() == "":
                st.error("❌ Please enter both email and password.")
            else:
                user = authenticate_user(email, password)

                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.session_state.last_activity = datetime.now()

                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials or account not approved.")

    # ---------------------------
    # REGISTER TAB
    # ---------------------------
    with tab2:
        st.markdown("### Create New Account")

        name = st.text_input("👤 Full Name")
        email = st.text_input("📧 Email")
        password = st.text_input("🔒 Password", type="password")
        confirm_password = st.text_input("🔒 Confirm Password", type="password")
        role = st.selectbox("👥 Register As", ["student", "teacher", "parent"])

        if role == "student":
            department = st.selectbox(
                "🏫 Department",
                ["Computer Science", "Electronics", "Mechanical", "Civil", "Other"]
            )
            year = st.selectbox("📅 Year", [1, 2, 3, 4])
            phone = st.text_input("📱 Phone")
        else:
            department = None
            year = None
            phone = None

        if st.button("📝 Register", use_container_width=True):
            errors = []

            if len(name) < 3:
                errors.append("Name must be at least 3 characters.")

            if not validate_email(email):
                errors.append("Invalid email format.")

            if len(password) < 6:
                errors.append("Password must be at least 6 characters.")

            if password != confirm_password:
                errors.append("Passwords do not match.")

            if errors:
                for error in errors:
                    st.error("❌ " + error)
            else:
                status, msg = register_user(
                    name,
                    email,
                    password,
                    role,
                    phone,
                    department,
                    year
                )

                if status:
                    st.success(f"✅ Registration successful! Your ID: **{msg}**")
                    st.info("⏳ Waiting for admin approval")
                    st.balloons()
                else:
                    st.error("❌ Registration failed: " + msg)