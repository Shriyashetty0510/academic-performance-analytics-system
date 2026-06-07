import streamlit as st
import pandas as pd
from config.database import execute_query


# =====================================================
# STUDENT DASHBOARD
# =====================================================

def student_dashboard(student_id):
    st.title("🏠 Student Dashboard")

    # Basic student info
    info = execute_query("""
        SELECT u.name, u.user_uid, sp.department, sp.year
        FROM users u
        LEFT JOIN student_profiles sp ON sp.user_id = u.id
        WHERE u.id = %s
    """, (student_id,))

    if info:
        st.success(f"🎓 {info[0]['department']} - Year {info[0]['year']}")

    col1, col2 = st.columns(2)

    # === LEFT: COURSE LIST ===
    with col1:
        st.subheader("📚 My Courses")
        courses = execute_query("""
            SELECT c.course_code, c.course_name
            FROM courses c
            JOIN student_courses sc ON sc.course_id = c.id
            WHERE sc.student_id = %s
        """, (student_id,))

        if courses:
            for c in courses:
                st.info(f"{c['course_code']} - {c['course_name']}")
        else:
            st.warning("Not enrolled in any courses.")

    # === RIGHT: Performance Summary ===
    with col2:
        st.subheader("📊 Performance Overview")

        # GPA summary
        gpa_result = execute_query("""
            SELECT AVG(gpa_value) AS gpa
            FROM grades
            WHERE student_id = %s
        """, (student_id,))

        if gpa_result and gpa_result[0]["gpa"] is not None:
            st.metric("🎯 GPA", f"{gpa_result[0]['gpa']:.2f}")
        else:
            st.info("No grades available yet.")

        # Attendance %
        att = execute_query("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END) AS present
            FROM attendance_records
            WHERE student_id = %s
        """, (student_id,))

        if att and att[0]["total"] > 0:
            percent = (att[0]["present"] / att[0]["total"]) * 100
            st.metric("📅 Attendance", f"{percent:.1f}%")
        else:
            st.info("No attendance records.")


# =====================================================
# VIEW ATTENDANCE
# =====================================================

def view_attendance(student_id):
    st.title("👁️ My Attendance")

    # Fetch student courses
    courses = execute_query("""
        SELECT c.id, c.course_code, c.course_name
        FROM courses c
        JOIN student_courses sc ON sc.course_id = c.id
        WHERE sc.student_id = %s
    """, (student_id,))

    if not courses:
        st.warning("You are not enrolled in any courses.")
        return

    course_map = {f"{c['course_code']} - {c['course_name']}": c["id"] for c in courses}

    selected = st.selectbox("Select Course", list(course_map.keys()))
    course_id = course_map[selected]

    # Fetch attendance records
    records = execute_query("""
        SELECT attendance_date, status
        FROM attendance_records
        WHERE student_id = %s AND course_id = %s
        ORDER BY attendance_date DESC
    """, (student_id, course_id))

    if not records:
        st.info("No attendance data found.")
        return

    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True)

    present_count = df[df["status"] == "Present"].shape[0]
    total = df.shape[0]
    percent = (present_count / total) * 100 if total > 0 else 0

    st.metric("Attendance %", f"{percent:.1f}%")


# =====================================================
# VIEW GRADES & GPA
# =====================================================

def view_grades(student_id):
    st.title("📊 My Grades & GPA")

    # Fetch grade records
    grades = execute_query("""
        SELECT c.course_code, c.course_name, g.grade, g.percent, g.gpa_value
        FROM grades g
        JOIN courses c ON g.course_id = c.id
        WHERE g.student_id = %s
    """, (student_id,))

    if not grades:
        st.warning("No grades available.")
        return

    df = pd.DataFrame(grades)

    # GPA summary
    avg_gpa = df["gpa_value"].mean()
    avg_percent = df["percent"].mean()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("🎯 Overall GPA", f"{avg_gpa:.2f} / 4.0")
    with col2:
        st.metric("📊 Average %", f"{avg_percent:.1f}%")

    st.markdown("---")
    st.dataframe(df, use_container_width=True)

    # Graph
    import plotly.express as px
    fig = px.bar(
        df,
        x="course_code",
        y="gpa_value",
        title="Course-Wise GPA",
        labels={"course_code": "Course", "gpa_value": "GPA"},
    )
    st.plotly_chart(fig, use_container_width=True)
