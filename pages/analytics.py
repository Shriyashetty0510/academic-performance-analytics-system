import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config.database import execute_query
from utils.helpers import log_activity


# =====================================================
# PREDICTIVE ANALYTICS — AT-RISK STUDENTS
# =====================================================

def predictive_analytics(user_id):
    st.title("📈 Predictive Analytics — At-Risk Students")

    st.info("This module identifies students at academic risk using GPA and attendance trends.")

    # Fetch GPA + Attendance Data
    at_risk = execute_query("""
        SELECT
            u.user_uid,
            u.id,
            u.name,
            ROUND(AVG(g.gpa_value), 2) AS gpa,
            ROUND(
                (SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) /
                 COUNT(a.id)) * 100,
            2) AS attendance_pct
        FROM users u
        LEFT JOIN grades g ON g.student_id = u.id
        LEFT JOIN attendance_records a ON a.student_id = u.id
        WHERE u.role='student' AND u.is_approved=TRUE
        GROUP BY u.id
        HAVING gpa < 2.5 OR attendance_pct < 75
        ORDER BY gpa ASC, attendance_pct ASC
    """)

    if not at_risk:
        st.success("🎉 No at-risk students found! All students are performing within safe ranges.")
        return

    df = pd.DataFrame(at_risk)

    # Risk Level Calculation
    def get_risk(row):
        if row["gpa"] < 2.0 or row["attendance_pct"] < 60:
            return "🔴 High Risk"
        elif row["gpa"] < 2.5 or row["attendance_pct"] < 75:
            return "🟡 Medium Risk"
        return "🟢 Low Risk"

    df["risk_level"] = df.apply(get_risk, axis=1)

    # Display Table
    st.warning(f"⚠️ {len(df)} student(s) identified as at-risk.")
    st.dataframe(df, use_container_width=True)

    # Scatter Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["attendance_pct"],
        y=df["gpa"],
        mode="markers+text",
        text=df["user_uid"],
        textposition="top center",
        marker=dict(size=12, color="red"),
        name="Students"
    ))

    fig.update_layout(
        title="🎯 Risk Assessment — GPA vs Attendance",
        xaxis_title="Attendance (%)",
        yaxis_title="GPA",
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Notify Button
    # Notify Button
    if st.button("📧 Notify Advisors / Teachers"):

        for student in df.itertuples():

        # Notify Teacher
            # Notify Teachers of Low-Performing Subjects

            teachers = execute_query("""
                SELECT DISTINCT c.teacher_id,
                c.course_name,
                g.gpa_value
                FROM grades g
                JOIN courses c
                   ON g.course_id = c.id
                WHERE g.student_id = %s
                   AND g.gpa_value < 2.5
            """, (student.id,))

            for teacher in teachers:

                execute_query("""
                    INSERT INTO notifications
                    (user_id, message, type, is_read)
                    VALUES (%s, %s, 'warning', FALSE)
                """, (
                    teacher["teacher_id"],
                    f"Student {student.name} ({student.user_uid}) is at risk in {teacher['course_name']} (GPA: {teacher['gpa_value']})."
                ), fetch=False)
        # Notify Parent
            parents = execute_query("""
                SELECT parent_id
                FROM parent_child_links
                WHERE child_id = %s
            """, (student.id,))

            for parent in parents:

                execute_query("""
                    INSERT INTO notifications
                    (user_id, message, type, is_read)
                    VALUES (%s, %s, 'warning', FALSE)
                """, (
                    parent["parent_id"],
                    f"Your child {student.name} ({student.user_uid}) is academically at risk."
                    ), fetch=False)

                log_activity(
                    user_id,
                    "risk_alert_sent",
                    f"Student={student.user_uid}"
                )

        st.success("Notifications sent to teachers and parents.")