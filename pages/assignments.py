import streamlit as st
import pandas as pd
from datetime import date, datetime
from config.database import execute_query
from utils.helpers import log_activity


# =====================================================
# ASSIGNMENT TRACKING MODULE
# =====================================================

def assignment_tracking(user):
    role = user["role"]

    if role == "teacher":
        teacher_assignments(user)

    elif role == "student":
        student_assignments(user["id"])

    else:
        st.error("Access denied.")


# =====================================================
# TEACHER VIEW
# =====================================================

def teacher_assignments(user):
    st.title("📝 Assignment Management")

    # Fetch courses taught by teacher
    courses = execute_query("""
        SELECT id, course_code, course_name
        FROM courses
        WHERE teacher_id = %s
    """, (user["id"],))

    if not courses:
        st.warning("You have no assigned courses.")
        return

    course_map = {f"{c['course_code']} - {c['course_name']}": c["id"] for c in courses}

    # Create assignment
    st.subheader("➕ Create Assignment")

    selected_course = st.selectbox("Select Course", list(course_map.keys()))
    course_id = course_map[selected_course]

    title = st.text_input("Assignment Title")
    description = st.text_area("Description")
    deadline = st.date_input("Deadline", min_value=date.today())

    if st.button("Create Assignment"):
        execute_query("""
            INSERT INTO assignments (course_id, title, description, deadline, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (course_id, title, description, deadline, user["id"]), fetch=False)

        log_activity(user["id"], "assignment_created", f"{title}")
        st.success("Assignment created successfully!")
        st.rerun()

    st.markdown("---")
    st.subheader("📂 Student Submissions")

    # Fetch submissions
    submissions = execute_query("""
        SELECT
            a.title,
            u.name AS student_name,
            asub.submitted_at,
            asub.status,
            a.deadline
        FROM assignment_submissions asub
        JOIN assignments a ON a.id = asub.assignment_id
        JOIN users u ON u.id = asub.student_id
        JOIN courses c ON c.id = a.course_id
        WHERE c.teacher_id = %s
        ORDER BY asub.submitted_at DESC
    """, (user["id"],))

    if submissions:
        df = pd.DataFrame(submissions)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No submissions yet.")


# =====================================================
# STUDENT VIEW
# =====================================================

def student_assignments(student_id):
    st.title("📘 My Assignments")

    # Fetch assignments for student courses
    assignments = execute_query("""
        SELECT
            a.id,
            a.title,
            a.description,
            a.deadline,
            c.course_name,
            asub.submitted_at,
            asub.status
        FROM assignments a
        JOIN courses c ON c.id = a.course_id
        JOIN student_courses sc ON sc.course_id = c.id
        LEFT JOIN assignment_submissions asub
            ON asub.assignment_id = a.id
            AND asub.student_id = %s
        WHERE sc.student_id = %s
        ORDER BY a.deadline ASC
    """, (student_id, student_id))

    if not assignments:
        st.info("No assignments available.")
        return

    for a in assignments:
        submitted = a["submitted_at"] is not None
        deadline_passed = a["deadline"] < date.today()

        # Status icon
        if submitted:
            icon = "✅"
        elif deadline_passed:
            icon = "⚠️"
        else:
            icon = "📌"

        with st.expander(f"{icon} {a['title']} - {a['course_name']}"):
            st.write(f"**Description:** {a['description']}")
            st.write(f"**Deadline:** {a['deadline']}")

            if submitted:
                st.success(f"Submitted on {a['submitted_at']}")

            elif deadline_passed:
                st.error("❌ Deadline passed! You cannot submit now.")

            else:
                if st.button("Submit Assignment", key=f"submit_{a['id']}"):
                    execute_query("""
                        INSERT INTO assignment_submissions
                        (assignment_id, student_id, submitted_at, status)
                        VALUES (%s, %s, %s, 'submitted')
                    """, (a["id"], student_id, datetime.now()), fetch=False)

                    log_activity(student_id, "assignment_submitted", f"{a['title']}")
                    st.success("Assignment submitted!")
                    st.rerun()
