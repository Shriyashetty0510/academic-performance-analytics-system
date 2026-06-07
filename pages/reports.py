import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from config.database import execute_query
from utils.helpers import log_activity


# =====================================================
# REPORTS & ANALYTICS
# =====================================================

def generate_reports(user):
    st.title("📊 Reports & Analytics")

    tab1, tab2 = st.tabs(["📅 Attendance Report", "🎯 GPA Report"])

    # ============================================================
    # TAB 1 — ATTENDANCE REPORT
    # ============================================================

    with tab1:
        st.subheader("📅 Attendance Report")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", value=date.today())

        if st.button("Generate Attendance Report"):
            data = execute_query("""
                SELECT
                    u.user_uid,
                    u.name,
                    COUNT(*) AS total_classes,
                    SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present,
                    ROUND((SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) AS percentage
                FROM attendance_records a
                JOIN users u ON a.student_id = u.id
                WHERE a.attendance_date BETWEEN %s AND %s
                GROUP BY u.id
                ORDER BY percentage ASC
            """, (start_date, end_date))

            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)

                # CSV Export
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    f"attendance_report_{start_date}_to_{end_date}.csv",
                    "text/csv"
                )

                log_activity(user["id"], "attendance_report_generated", "Date range report")
            else:
                st.info("No attendance data found for this period.")

    # ============================================================
    # TAB 2 — GPA REPORT
    # ============================================================

    with tab2:
        st.subheader("🎯 GPA Report")

        if st.button("Generate GPA Report"):
            data = execute_query("""
            SELECT
               u.user_uid,
               u.name,
               sp.department,
               sp.year,
               ROUND(COALESCE(AVG(g.gpa_value), 0), 2) AS gpa,
               COUNT(g.course_id) AS courses
            FROM users u
            LEFT JOIN student_profiles sp
              ON sp.user_id = u.id
            LEFT JOIN grades g
              ON g.student_id = u.id
            WHERE u.role='student'
              AND u.is_approved=TRUE
            GROUP BY
                u.id,
                u.user_uid,
                u.name,
                sp.department,
                sp.year
            ORDER BY gpa DESC
           """)

            if data:
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)

                # Histogram
                fig = px.histogram(df, x="gpa", nbins=20, title="GPA Distribution")
                st.plotly_chart(fig, use_container_width=True)

                # CSV download
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download GPA CSV",
                    csv,
                    "gpa_report.csv",
                    "text/csv"
                )

                log_activity(user["id"], "gpa_report_generated")
            else:
                st.warning("No GPA data available.")
