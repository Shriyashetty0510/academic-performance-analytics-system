import streamlit as st
import pandas as pd
from datetime import date, datetime
from config.database import execute_query
from utils.helpers import log_activity


# =====================================================
# TEACHER DASHBOARD
# =====================================================

def teacher_dashboard(teacher_id):
    st.title("🏠 Teacher Dashboard")

    st.subheader("📚 My Courses")

    courses = execute_query("""
        SELECT course_code, course_name
        FROM courses
        WHERE teacher_id = %s
    """, (teacher_id,))

    if courses:
        for c in courses:
            st.success(f"{c['course_code']} - {c['course_name']}")
    else:
        st.info("No courses assigned.")


# =====================================================
# MARK ATTENDANCE
# =====================================================

def mark_attendance(teacher_id):
    st.title("📝 Mark Attendance")

    # Fetch teacher's courses
    courses = execute_query("""
        SELECT id, course_code, course_name
        FROM courses
        WHERE teacher_id = %s
    """, (teacher_id,))

    if not courses:
        st.warning("No courses assigned.")
        return

    course_map = {f"{c['course_code']} - {c['course_name']}": c["id"] for c in courses}

    selected_course = st.selectbox("Select Course", list(course_map.keys()))
    course_id = course_map[selected_course]

    # Fetch students enrolled in course
    students = execute_query("""
        SELECT u.id, u.user_uid, u.name
        FROM users u
        JOIN student_courses sc ON sc.student_id = u.id
        WHERE sc.course_id = %s
    """, (course_id,))

    if not students:
        st.warning("No students enrolled in this course.")
        return

    attendance_date = st.date_input("Select Date", date.today())
    attendance = {}

    st.subheader("Mark Attendance")

    for student in students:
        status = st.radio(
            f"{student['user_uid']} - {student['name']}",
            ["Present", "Absent", "Late"],
            horizontal=True,
            key=f"att_{student['id']}"
        )
        attendance[student["id"]] = status

    if st.button("Save Attendance"):
        for student_id, status in attendance.items():
            execute_query("""
                INSERT INTO attendance_records (student_id, course_id, teacher_id, attendance_date, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (student_id, course_id, teacher_id, attendance_date, status), fetch=False)

        log_activity(teacher_id, "attendance_marked", f"Course={selected_course}")
        st.success("Attendance saved successfully!")


# =====================================================
# ENTER GRADES
# =====================================================

def enter_grades(teacher_id):
    st.title("📊 Enter Grades")

    # Fetch courses
    courses = execute_query("""
        SELECT id, course_code, course_name
        FROM courses
        WHERE teacher_id = %s
    """, (teacher_id,))

    if not courses:
        st.warning("No courses assigned.")
        return

    course_map = {f"{c['course_code']} - {c['course_name']}": c["id"] for c in courses}

    selected_course = st.selectbox("Select Course", list(course_map.keys()))
    course_id = course_map[selected_course]

    # Fetch students
    students = execute_query("""
        SELECT u.id, u.user_uid, u.name
        FROM users u
        JOIN student_courses sc ON sc.student_id = u.id
        WHERE sc.course_id = %s
    """, (course_id,))

    if not students:
        st.warning("No students enrolled.")
        return

    st.subheader("Enter Grades")

    for student in students:
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.write(f"{student['user_uid']} - {student['name']}")

        with col2:
            percent = st.number_input(
                "Percentage",
                min_value=0,
                max_value=100,
                key=f"pct_{student['id']}",
                label_visibility="collapsed"
            )

        # Grade logic
        if percent >= 90:
            grade, gpa = "A+", 4.0
        elif percent >= 80:
            grade, gpa = "A", 4.0
        elif percent >= 70:
            grade, gpa = "B+", 3.5
        elif percent >= 60:
            grade, gpa = "B", 3.0
        elif percent >= 50:
            grade, gpa = "C", 2.0
        else:
            grade, gpa = "F", 0.0

        with col3:
            if st.button("Save", key=f"save_{student['id']}"):
                execute_query("""
                    INSERT INTO grades (student_id, course_id, grade, percent, gpa_value)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        grade = VALUES(grade),
                        percent = VALUES(percent),
                        gpa_value = VALUES(gpa_value)
                """, (student["id"], course_id, grade, percent, gpa), fetch=False)

                log_activity(teacher_id, "grade_entered",
                             f"Student={student['user_uid']}, Grade={grade}")

                st.success(f"Saved {student['name']}'s grade!")
