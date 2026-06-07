import streamlit as st

# Authentication
from pages.login import login_page
from auth.auth_service import authenticate_user
from auth.session import initialize_session, check_session_timeout, logout

# Admin Pages
from pages.admin import (
    admin_dashboard,
    approve_users,
    manage_courses,
    parent_management,
    bulk_import_export,
)

# Teacher Pages
from pages.teacher import (
    teacher_dashboard,
    mark_attendance,
    enter_grades,
)

# Student Pages
from pages.student import (
    student_dashboard,
    view_attendance,
    view_grades,
)

# Parent Pages
from pages.parent import parent_dashboard

# Reports & Analytics
from pages.reports import generate_reports
from pages.analytics import predictive_analytics

# Assignments
from pages.assignments import assignment_tracking

# Notifications
from pages.notifications import notifications_center


# =========================================================
# MAIN NAVIGATION BASED ON ROLE
# =========================================================

def create_navigation(role):
    if role == "admin":
        return st.radio(
            "📋 Navigation",
            [
        "🏠 Dashboard",
        "📋 Approve Users",
        "📚 Manage Courses",
        "👨‍👩‍👧 Parent Management",
        "📦 Bulk Operations",
        "📊 Reports",
        "📈 Analytics",
        "🔔 Notifications"
        ],
            label_visibility="collapsed",
        )

    elif role == "teacher":
        return st.radio(
            "📋 Navigation",
            [
                "🏠 Dashboard",
                "📝 Mark Attendance",
                "📊 Enter Grades",
                "📝 Assignments",
                "📊 Reports",
                "🔔 Notifications"
            ],
            label_visibility="collapsed",
        )

    elif role == "student":
        return st.radio(
            "📋 Navigation",
            [
                "🏠 Dashboard",
                "👁️ View Attendance",
                "📊 My Grades & GPA",
                "📝 Assignments",
                "🔔 Notifications"
            ],
            label_visibility="collapsed",
        )

    elif role == "parent":
        return st.radio(
            "📋 Navigation",
            [
                "🏠 Dashboard",
                "📊 Child's Performance",
                "🔔 Notifications"
            ],
            label_visibility="collapsed",
        )


# =========================================================
# ROUTER — OPEN CORRECT PAGE
# =========================================================

def route_page(page, user):
    role = user["role"]

    if page == "🏠 Dashboard":
        if role == "admin":
            admin_dashboard()
        elif role == "teacher":
            teacher_dashboard(user["id"])
        elif role == "student":
            student_dashboard(user["id"])
        elif role == "parent":
            parent_dashboard(user["id"])

    elif page == "📋 Approve Users":
        approve_users()

    elif page == "📚 Manage Courses":
        manage_courses()
        
    elif page == "👨‍👩‍👧 Parent Management":
        parent_management()

    elif page == "📦 Bulk Operations":
        bulk_import_export()

    elif page == "📝 Mark Attendance":
        mark_attendance(user["id"])

    elif page == "📊 Enter Grades":
        enter_grades(user["id"])

    elif page == "👁️ View Attendance":
        view_attendance(user["id"])

    elif page == "📊 My Grades & GPA":
        view_grades(user["id"])

    elif page == "📊 Child's Performance":
        parent_dashboard(user["id"])

    elif page == "📝 Assignments":
        assignment_tracking(user)

    elif page == "📊 Reports":
        generate_reports(user)

    elif page == "📈 Analytics":
        predictive_analytics(user["id"])

    elif page == "🔔 Notifications":
        notifications_center(user["id"])

    else:
        st.error("❌ Page not found")


# =========================================================
# MAIN APPLICATION
# =========================================================

def main():
    st.set_page_config(
        page_title="APAS - Academic Performance Analytics",
        page_icon="🎓",
        layout="wide"
    )

    initialize_session(st)

    # If NOT logged in → show login page
    if not st.session_state.logged_in:
        login_page()
        return

    # Check timeout
    if not check_session_timeout(st):
        return

    user = st.session_state.user

    # SIDEBAR
    with st.sidebar:
        st.title("🎓 APAS")
        st.markdown("---")

        st.markdown(f"### Welcome, {user['name']}!")
        st.caption(f"Role: {user['role'].title()}")
        st.caption(f"ID: {user['user_uid']}")

        st.markdown("---")

        page = create_navigation(user["role"])

        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True):
            logout(st)
            st.rerun()

        st.markdown("---")
        st.caption("© 2025 APAS System")

    # Route correct page
    route_page(page, user)


if __name__ == "__main__":
    main()
