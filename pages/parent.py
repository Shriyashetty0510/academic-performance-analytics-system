import streamlit as st
import pandas as pd
from config.database import execute_query


# =====================================================
# PARENT DASHBOARD
# =====================================================

def parent_dashboard(parent_id):
    st.title("👨‍👩‍👧 Parent Dashboard")

    # Fetch children linked to parent
    children = execute_query("""
        SELECT u.id, u.name, u.user_uid
        FROM users u
        JOIN parent_child_links pcl ON pcl.child_id = u.id
        WHERE pcl.parent_id = %s
    """, (parent_id,))

    if not children:
        st.warning("No child accounts are linked to your profile.")
        st.info("Please contact admin to add your child.")
        return

    # Dropdown to choose child
    child_map = {f"{c['user_uid']} - {c['name']}": c["id"] for c in children}
    selected_child = st.selectbox("Select Child", list(child_map.keys()))
    child_id = child_map[selected_child]

    # Layout
    col1, col2 = st.columns(2)

    # =====================================================
    # GPA SUMMARY
    # =====================================================
    with col1:
        st.subheader("📊 Academic Performance")

        gpa_res = execute_query("""
            SELECT AVG(gpa_value) AS gpa
            FROM grades
            WHERE student_id = %s
        """, (child_id,))

        if gpa_res and gpa_res[0]["gpa"] is not None:
            st.metric("GPA", f"{gpa_res[0]['gpa']:.2f}")
        else:
            st.info("No grade data available.")

    # =====================================================
    # ATTENDANCE SUMMARY
    # =====================================================
    with col2:
        st.subheader("📅 Attendance Summary")

        attendance = execute_query("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present
            FROM attendance_records
            WHERE student_id = %s
        """, (child_id,))

        if attendance and attendance[0]["total"] > 0:
            percent = (attendance[0]["present"] / attendance[0]["total"]) * 100
            st.metric("Attendance", f"{percent:.1f}%")
        else:
            st.info("No attendance records found.")

    # =====================================================
    # RECENT GRADES
    # =====================================================

    st.subheader("📚 Recent Grades")

    grades = execute_query("""
        SELECT c.course_name, g.grade, g.percent
        FROM grades g
        JOIN courses c ON g.course_id = c.id
        WHERE g.student_id = %s
        ORDER BY g.created_at DESC
        LIMIT 5
    """, (child_id,))

    if grades:
        df = pd.DataFrame(grades)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No grade data available.")
